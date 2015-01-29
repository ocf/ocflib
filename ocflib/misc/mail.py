"""Email handling and sending"""

import email.mime.text
import subprocess
from email.utils import parseaddr

import ocflib.constants as constants
import ocflib.misc.validators as validators


def send_mail(to, subject, body, sender=constants.MAIL_FROM):
    """Send a plain-text mail message.

    `body` should be a string with newlines, wrapped at about 80 characters."""

    if not validators.valid_email(parseaddr(sender)[1]):
        raise ValueError("Invalid sender address.")

    if not validators.valid_email(parseaddr(to)[1]):
        raise ValueError("Invalid recipient address.")

    msg = email.mime.text.MIMEText(body)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to

    # we send the message via sendmail, since we may one day prohibit traffic
    # to port 25 that doesn't go via the system mailserver
    p = subprocess.Popen((constants.SENDMAIL_PATH, '-t', '-oi'),
                         stdin=subprocess.PIPE)
    p.communicate(msg.as_string().encode('utf8'))
