"""Email handling and sending"""
import email.mime.text
import inspect
import socket
import subprocess
from email.utils import parseaddr

import ocflib.account.validators
import ocflib.constants as constants
import ocflib.misc.validators as validators


def email_for_user(username):
    """Return email for a user.

    Currently, just appends @ocf.berkeley.edu, but could eventually do
    something more complicated."""

    ocflib.account.validators.validate_username(username, check_exists=True)
    return '{}@ocf.berkeley.edu'.format(username)


def send_mail_user(user, subject, body, sender=constants.MAIL_FROM):
    """Send a plan-text mail message to a user."""
    send_mail(email_for_user(user), subject, body, sender=sender)


def send_mail(to, subject, body, sender=constants.MAIL_FROM):
    """Send a plain-text mail message.

    `body` should be a string with newlines, wrapped at about 80 characters."""

    if not validators.valid_email(parseaddr(sender)[1]):
        raise ValueError('Invalid sender address.')

    if not validators.valid_email(parseaddr(to)[1]):
        raise ValueError('Invalid recipient address.')

    msg = email.mime.text.MIMEText(body)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to

    # we send the message via sendmail, since we may one day prohibit traffic
    # to port 25 that doesn't go via the system mailserver
    p = subprocess.Popen((constants.SENDMAIL_PATH, '-t', '-oi'),
                         stdin=subprocess.PIPE)
    p.communicate(msg.as_string().encode('utf8'))


def send_problem_report(problem):
    """Send a problem report to OCF staff."""

    def format_frame(frame):
        _, filename, line, funcname, _, _ = frame
        return '{}:{} ({})'.format(filename, line, funcname)

    callstack = '\n        by '.join(map(format_frame, inspect.stack()))
    body = \
        """A problem was encountered and reported via ocflib:

{problem}

====
Hostname: {hostname}
Callstack:
    at {callstack}
""".format(problem=problem, hostname=socket.getfqdn(), callstack=callstack)

    send_mail(
        constants.MAIL_ROOT,
        '[ocflib] Problem report from ' + socket.getfqdn(),
        body)
