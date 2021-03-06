#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
from urlparse import urlparse
import cgi
import sys
import os
import subprocess
import logging

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium import common
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.encoders import encode_base64

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from functools import wraps
from flask import request, Response

from createabook_config import *

def check_auth(username, password):
    return username == HTTP_AUTH_LOGIN and password == HTTP_AUTH_PASSWD

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

class WebDrivers:
    Firefox, RemoteChrome = range(2)
    
app = Flask(__name__)
logging.basicConfig(filename='createabook.log',level=logging.DEBUG)

app.config.update(dict(
    DEBUG=not EXTERNALLY_VISIBLE_SERVER,
    SECRET_KEY='development key',
    DEFAULT_KINDLE_EMAIL=DEFAULT_KINDLE_EMAIL,
    FORM_FIELD_FROM_EMAIL=not FROM_EMAIL,
    FORM_FIELD_SMTP_SERVER=not SMTP_SERVER,
    FORM_FIELD_SMTP_USERNAME=not SMTP_USERNAME,
    FORM_FIELD_SMTP_PASSWORD=not SMTP_PASSWORD
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route("/")
@requires_auth
def wiki_to_kindle_form():
    """Form for wiki_to_kindle
    """
    return render_template('wiki_to_kindle_form.html', \
        default_kindle_email = app.config['DEFAULT_KINDLE_EMAIL'], \
        form_field_from_email = app.config['FORM_FIELD_FROM_EMAIL'], \
        form_field_smtp_server = app.config['FORM_FIELD_SMTP_SERVER'], \
        form_field_smtp_username = app.config['FORM_FIELD_SMTP_USERNAME'], \
        form_field_smtp_password = app.config['FORM_FIELD_SMTP_PASSWORD'])
    
@app.route('/wiki-to-kindle', methods=['POST'])
def wiki_to_kindle_handler():
    """Handler for wiki_to_kindle form
    """
    article_urls = request.form['article_urls'].splitlines()
    logging.debug('article_urls: {0}'.format(repr(article_urls)))
    book_title = request.form['book_title']
    book_subtitle = request.form['book_subtitle']
    convert_to_mobi = 'convert_to_mobi' in request.form
    logging.debug('convert_to_mobi: {0}'.format(convert_to_mobi))
    
    kindle_email = DEFAULT_KINDLE_EMAIL
    if 'kindle_email' in request.form:
        kindle_email = request.form['kindle_email']
        
    from_email = FROM_EMAIL
    if app.config['FORM_FIELD_FROM_EMAIL'] \
    and 'from_email' in request.form:
        from_email = request.form['from_email']
        
    smtp_server = SMTP_SERVER
    if app.config['FORM_FIELD_SMTP_SERVER'] \
    and 'smtp_server' in request.form:
        smtp_server = request.form['smtp_server']
        
    smtp_username = SMTP_USERNAME
    if app.config['FORM_FIELD_SMTP_USERNAME'] \
    and 'smtp_username' in request.form:
        smtp_username = request.form['smtp_username']
        
    smtp_password = SMTP_PASSWORD
    if app.config['FORM_FIELD_SMTP_PASSWORD'] \
    and 'smtp_password' in request.form:
        smtp_password = request.form['smtp_password']
        
    wiki_to_kindle(article_urls, book_title, book_subtitle, \
        kindle_email, from_email, smtp_server, smtp_username, smtp_password, \
        convert_to_mobi)
    flash('Done.')
    return redirect(url_for('wiki_to_kindle_form'))

def get_wiki_url(driver, article_url):
    """If a mobile wikipedia URL is given, clicks through to the desktop version.
    Returns article_url, wiki
    E.g. normalize_url('http://fr.m.wikipedia.org/wiki/Philosophie') =>
    'http://fr.wikipedia.org/w/index.php?title=Philosophie', 'fr.wikipedia.org'
    """
    driver.get(article_url)
    #check for mobile wikipedia
    if article_url.find('m.wikipedia.org') != -1:
        #click desktop version link
        a = driver.find_element_by_id("mw-mf-display-toggle")
        a.click()
        driver.implicitly_wait(1)
    article_url = driver.current_url
    wiki = urlparse(article_url).netloc # e.g. "fr.wikipedia.org"
    logging.debug('wiki: {0}'.format(wiki))
    return article_url, wiki
    
def create_a_book(article_urls, book_title, book_subtitle="", book_fmt="epub", \
    webdriverType=WebDrivers.Firefox):
    """Create and download and ebook version of the specified WikiMedia article
    
    Limitations: 
        Eventually, support will be added for multiple articles per book
        however you cannot mix articles from different language Wikipedias, i.e. 
        cannot put an en.wikipedia.org article and an fr.wikipedia.org article in 
        the same book.
        
    Args:
        article_urls [list of str]
            Complete wikipedia article URLs
        book_title [str]
            Desired book title (is also used for output filename)
        book_subtitle [str]
            Desired book subtitle (optional)
        book_fmt [str]
            "epub" (default) = e-book (EPUB)
            "pdf" = e-book (PDF)
            "odf" = traitement de texte (OpenDocument)
            "zim" = Kiwix (OpenZIM)
        webdriver
            WebDrivers.Firefox Built-in Firefox WebDriver
            WebDrivers.RemoteChrome Remote WebDriver for ChromeDriver on port 9515
    Returns:
        local_filename [str]
            Local filename of the downloaded ebook file
    """
    if len(article_urls) == 0:
        logging.error('create_a_book: article_urls is empty, nothing to do')
        return
    article_url = article_urls.pop(0)
    driver = None
    if webdriverType == WebDrivers.Firefox:
        driver = webdriver.Firefox()
    elif webdriverType == WebDrivers.RemoteChrome:
        driver = webdriver.Remote(
           command_executor='http://localhost:9515',
           desired_capabilities=DesiredCapabilities.CHROME)

    article_url, wiki = get_wiki_url(driver, article_url)

    #h3 = driver.find_element_by_id("p-coll-print_export-label")
    #a = h3.find_element_by_tag_name("a") 
    #a.click() # cliquer "Imprimer / exporter"
    #driver.implicitly_wait(1)
    while True:
        try:
            div = driver.find_element_by_id("p-coll-print_export")
            li = div.find_element_by_id("coll-create_a_book")
            a = li.find_element_by_tag_name("a")
            a.click() # cliquer "Créer un livre"
            break
        except:
            logging.debug('Caught {0} Retrying... '.format(sys.exc_info()[0]))
            driver.implicitly_wait(1)

    driver.implicitly_wait(3)
    div = driver.find_element_by_class_name("ok")
    a = div.find_element_by_tag_name("a")
    a.click() # cliquer "Démarrer le créateur de livres"

    a = driver.find_element_by_id("coll-add_article")
    a.click() # cliquer "Ajouter cette page à votre livre"
    
    # Add the rest of the articles to the book
    while len(article_urls):
        article_url = article_urls.pop(0)
        article_url, wiki = get_wiki_url(driver, article_url)
        a = driver.find_element_by_id("coll-add_article")
        a.click() # cliquer "Ajouter cette page à votre livre"

    # click "Show book (1 page)" (seems to work for any lang wikipedia)
    driver.get("http://" + wiki + "/wiki/Special:Book")

    title_txt = driver.find_element_by_id("titleInput") # "Titre"
    title_txt.send_keys(book_title)
    subtitle_txt = driver.find_element_by_id("subtitleInput") # "Sous-titre"
    subtitle_txt.send_keys(book_subtitle)
    select = Select(driver.find_element_by_id("formatSelect")) # "Format"
    option_value = book_fmt
    if book_fmt == 'pdf':
        option_value = 'rl'
    select.select_by_value(option_value)
    btn = driver.find_element_by_id("downloadButton") # "Télécharger
    btn.click()

    url = ''
    while True:
        try:
            div = driver.find_element_by_id("mw-content-text")
            a = div.find_element_by_tag_name("a") # "Télécharger le fichier"
            url = a.get_attribute("href")
            if url.find("bookcmd=download") != -1:
                logging.debug("found bookcmd=download")
                logging.debug("url: {0}".format(url)) 
                #a.click() #Télécharger
                break
        except:
            logging.debug('Caught {0} Retrying... '.format(sys.exc_info()[0]))
            driver.implicitly_wait(1)
    filename = ''
    try:
        req = urllib2.Request(url=url)
        resp = urllib2.urlopen(req)
        _, params = cgi.parse_header(resp.headers.get('Content-Disposition', ''))
        filename = params['filename']
        logging.debug('Content-Disposition filename: {0}'.format(filename))
        with open(filename, 'wb') as f:
            f.write(resp.read())
    except:
        logging.error('Error: {0}'.format(sys.exc_info()[0]))
    driver.close()
    return filename
    
def convert_x_to_mobi(filename):
    """Convert EPUB (or other) to MOBI
    expects 'ebook-convert.exe' directory to be in your system path
    e.g. C:\Program Files (x86)\Calibre2
    """
    if os.path.isfile(filename):
        mobi_filename = os.path.splitext(filename)[0] + '.mobi'
        cmd = 'ebook-convert.exe'
        args = [filename, mobi_filename]
        logging.debug('cmd: {0}'.format(cmd))
        logging.debug('args: {0}'.format(repr(args)))
        output = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE).communicate()[0]
        logging.debug('output:\r\n{0}'.format(output))
        return mobi_filename
    else:
        return False
    
def email_ebook(filename, from_email, to_addr, subject, smtp_server, smtp_username, smtp_password):
    """Email an ebook file to a given address using the specified SMTP server
    """
    mroot = MIMEMultipart('related')
    mroot['Subject'] = subject
    mroot['From'] = from_email
    mroot['To'] = to_addr
    with open(filename, 'rb') as f:
        m = MIMEBase('application', 'octet-stream')
        m.set_payload(open(filename, 'rb').read())
        encode_base64(m)
        m.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(filename))
        mroot.attach(m)
    smtp = smtplib.SMTP()
    smtp.connect(smtp_server)
    smtp.starttls()
    smtp.login(smtp_username, smtp_password)
    smtp.sendmail(from_email, to_addr, mroot.as_string())
    smtp.quit()
    
def wiki_to_kindle(article_urls, book_title, book_subtitle, \
    kindle_email, from_email, smtp_server, smtp_username, smtp_password, \
    convert_to_mobi=True):
    """Create and download and ebook version of the specified WikiMedia article,
    covert it from EPUB to MOBI format, and email it directly to a kindle.
    
    Args:
        convert_to_mobi
            Convert ebook to MOBI format (Kindle does not support EPUB)
    Returns:
    Raises:
    """
    epub_filename = create_a_book(article_urls, book_title, book_subtitle)
    email_filename = epub_filename
    if convert_to_mobi:
        email_filename = convert_x_to_mobi(epub_filename)
    email_subject = book_title
    if len(book_subtitle):
        email_subject += u' - {0}'.format(book_subtitle)
    email_ebook(email_filename, from_email, kindle_email, email_subject, \
                smtp_server, smtp_username, smtp_password)
    
if __name__ == '__main__':
    # Start the Flask server
    if EXTERNALLY_VISIBLE_SERVER:
        app.run(host='0.0.0.0')
    else:
        app.run()