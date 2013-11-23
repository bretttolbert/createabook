createabook
===========

Automation of WikiMedia Book Creator Feature, Calibre EPUB to MOBI conversion, and email to Kindle

Dependencies:
Python 2.7.x
    http://www.python.org/getit/
selenium
    http://www.seleniumhq.org/
    pip install selenium
flask
    http://flask.pocoo.org/docs/installation/
    pip install Flask

Usage:
To start the server, just run createabook.py
The Create A Book form should then be visible at http://localhost:5000/
If you want the server to be externally visible, change EXTERNALY_VISIBLE_SERVER to True.

Gotchas:
The from email must be in your Amazon Kindle "Approved Personal Document E-mail List"
On the left side of your "Manage Your Kindle" page should be a box marked "Your Kindle Account", 
and within that box will be "Personal Document Settings". You'll find it there..

FAQ
Q: Why have a web interface, instead of a standalone GUI or CLI?
A: Because I want to run the server on my desktop and use the web interface 
from my Android phone or any other device.

