createabook
===========

Automation of WikiMedia Book Creator Feature, Calibre EPUB to MOBI conversion, and email to Kindle

Written in Python and uses the Selenium web browser automation library and the Flask microframework. 
It uses the Calibre ebook-covert utility to do the conversion.

Screenshot: http://i.imgur.com/fwj3kZQ.png

There may or may not be a live demo running at the moment at http://bretttolbert.dyndns.org:5000/ but don't expect it to stay up. FROM_EMAIL is createabook.py@gmail.com

Blog post: http://www.bretttolbert.com/2013/11/23/createabook-py-web-app-to-automate-wikipedias-book-creator-feature-download-convert-from-epub-to-mobi-and-email-to-kindle/

Reddit: http://www.reddit.com/r/kindle/comments/1radef/web_app_to_automate_wikipedias_book_creator/

Please share!

Dependencies:
* Python 2.7.X - http://www.python.org/getit/
* selenium - http://www.seleniumhq.org/ pip install selenium
* flask http://flask.pocoo.org/docs/installation/ pip install Flask
* ebook-covert.exe (included with Calibre) http://calibre-ebook.com/download 
The directory containing ebook-convert.exe (e.g. C:\Program Files (x86)\Calibre2) must be added to your system path. how to: http://www.computerhope.com/issues/ch000549.htm

Usage:
To start the server, just run createabook.py
The Create A Book form should then be visible at http://localhost:5000/

Configuration:
There are several variables in createabook.py which can be configured to your liking.

EXTERNALY_VISIBLE_SERVER - Controls whether the server is externally visible. 
There is logic to automatically disable Flask debug mode if this flag is set to True for security reasons.

I reccommend that you set FROM_EMAIL, SMTP_SERVER, SMTP_USERNAME, and SMTP_PASSWORD in the script,
but if you leave them set to empty, then it will show form fields for these items. 

Gotchas:
The from email must be in your Amazon Kindle "Approved Personal Document E-mail List"
On the left side of your "Manage Your Kindle" page should be a box marked "Your Kindle Account", 
and within that box will be "Personal Document Settings". You'll find it there..

FAQ
Q: Why have a web interface, instead of a standalone GUI or CLI?
A: Because I want to run the server on my desktop and use the web interface 
from my Android phone or any other device.

