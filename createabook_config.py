#All fields are required, but empty is a valid value, which means a 
#form field will be displayed for that input.
#The kindle email form field is always displayed, but you can specify
#a default kindle email which is used as the default value of the form field.
#For the other inputs, if you define set the value here, the form field will
#not be displayed.
DEFAULT_KINDLE_EMAIL = 'user@kindle.com'   # Kindle email address (e.g. 'mykindle@amazon.com')
FROM_EMAIL = ''     # This email must be in your Amazon Kindle approved sender list
SMTP_SERVER = '' # SMTP server for FROM_EMAIL account e.g. smtp.gmail.com:587
SMTP_USERNAME = ''  # SMTP username for FROM_EMAIL account
SMTP_PASSWORD = ''  # SMTP password for FROM_EMAIL account
EXTERNALLY_VISIBLE_SERVER = True
#Credentials for HTTP Basic Auth
HTTP_AUTH_LOGIN = 'admin'
HTTP_AUTH_PASSWD = 'secret'