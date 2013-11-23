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

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.encoders import encode_base64

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)

KINDLE_EMAIL = ''   # Kindle email address (e.g. 'mykindle@amazon.com')
FROM_EMAIL = ''     # This email must be in your Amazon Kindle approved sender list
SMTP_SERVER = 'smtp.gmail.com:587' # SMTP server for FROM_EMAIL account
SMTP_USERNAME = ''  # SMTP username for FROM_EMAIL account
SMTP_PASSWORD = ''  # SMTP password for FROM_EMAIL account
EXTERNALY_VISIBLE_SERVER = False

app.config.update(dict(
    DEBUG=not EXTERNALY_VISIBLE_SERVER,
    SECRET_KEY='development key',
    FORM_FIELD_FROM_EMAIL=not FROM_EMAIL,
    FORM_FIELD_SMTP_SERVER=not SMTP_SERVER,
    FORM_FIELD_SMTP_USERNAME=not SMTP_USERNAME,
    FORM_FIELD_SMTP_PASSWORD=not SMTP_PASSWORD
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

@app.route("/")
def wiki_to_kindle_form():
    """Form for wiki_to_kindle
    """
    return render_template('wiki_to_kindle_form.html', \
        form_field_from_email = app.config['FORM_FIELD_FROM_EMAIL'], \
        form_field_smtp_server = app.config['FORM_FIELD_SMTP_SERVER'], \
        form_field_smtp_username = app.config['FORM_FIELD_SMTP_USERNAME'], \
        form_field_smtp_password = app.config['FORM_FIELD_SMTP_PASSWORD'])
    
@app.route('/wiki-to-kindle', methods=['POST'])
def wiki_to_kindle_handler():
    """Handler for wiki_to_kindle form
    """
    article_url = request.form['article_url']
    book_title = request.form['book_title']
    book_subtitle = request.form['book_subtitle']
    
    kindle_email = KINDLE_EMAIL
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
        
    wiki_to_kindle(article_url, book_title, book_subtitle, \
        kindle_email, from_email, smtp_server, smtp_username, smtp_password)
    flash('Done.')
    return redirect(url_for('wiki_to_kindle_form'))

logging.basicConfig(filename='createabook.log',level=logging.DEBUG)
#logging.getLogger().addHandler(logging.StreamHandler()) # print to stderr as well

def create_a_book(article_url, book_title, book_subtitle="", book_fmt="epub"):
    """Create and download and ebook version of the specified WikiMedia article
    article_url = Complete wikipedia article URL
    book_title = Desired book title (is also used for output filename)
    book_subtitle = Desired book subtitle (optional)
    book_fmt = "epub" | "pdf" | "odf" | "zim"
        epub = e-book (EPUB)
        pdf = e-book (PDF)
        odf = traitement de texte (OpenDocument)
        zim = Kiwix (OpenZIM)
    return: local_filename
    Limitations: Eventually, support will be added for multiple articles per book
    however you cannot mix articles from different language Wikipedias, i.e. 
    cannot put an en.wikipedia.org article and an fr.wikipedia.org article in 
    the same book.
    """
    wiki = urlparse(article_url).netloc # e.g. "fr.wikipedia.org"
    logging.debug('wiki: {0}'.format(wiki))
    driver = webdriver.Firefox()
    driver.get(article_url)
    h3 = driver.find_element_by_id("p-coll-print_export-label")
    a = h3.find_element_by_tag_name("a") 
    a.click() # cliquer "Imprimer / exporter"
    driver.implicitly_wait(1)
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
    
def convert_to_mobi(filename):
    """Convert EPUB (or other) to MOBI
    expects 'ebook-convert.exe' directory to be in your system path
    e.g. C:\Program Files (x86)\Calibre2
    """
    mobi_filename = os.path.splitext(filename)[0] + '.mobi'
    cmd = 'ebook-convert.exe'
    args = [filename, mobi_filename]
    logging.debug('cmd: {0}'.format(cmd))
    logging.debug('args: {0}'.format(repr(args)))
    output = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE).communicate()[0]
    logging.debug('output:\r\n{0}'.format(output))
    return mobi_filename
    
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
    
def wiki_to_kindle(article_url, book_title, book_subtitle, kindle_email, from_email, smtp_server, smtp_username, smtp_password):
    """Create and download and ebook version of the specified WikiMedia article,
    covert it from EPUB to MOBI format, and email it directly to a kindle.
    """
    epub_filename = create_a_book(article_url, book_title, book_subtitle)
    mobi_filename = convert_to_mobi(epub_filename)
    email_subject = book_title
    if len(book_subtitle):
        email_subject += u' - {0}'.format(book_subtitle)
    email_ebook(mobi_filename, from_email, kindle_email, email_subject, smtp_server, smtp_username, smtp_password)
    
if __name__ == '__main__':
    # Start the Flask server
    if EXTERNALY_VISIBLE_SERVER:
        app.run(host='0.0.0.0')
    else:
        app.run()