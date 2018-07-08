"""Email handling and sending"""
import email.mime.text
import inspect
import socket
import subprocess
from email.utils import parseaddr

from jinja2 import Environment
from jinja2 import PackageLoader

import ocflib.misc.validators as validators

SENDMAIL_PATH = '/usr/sbin/sendmail'
MAIL_ROOT = 'root@ocf.berkeley.edu'

MAIL_ROOT = 'root@ocf.berkeley.edu'
MAIL_FROM = 'Open Computing Facility <help@ocf.berkeley.edu>'
MAIL_SIGNATURE = """Thanks for flying OCF,
The friendly staff of 171 MLK Student Union

=========
The Open Computing Facility is an all-volunteer, student-run service
group providing free printing, web hosting, disk space, and Unix shell
accounts.

We love free & open-source software. Sound like you? Get involved!
    https://ocf.io/staff

OCF volunteers hold weekly staff hours to provide support:
    https://ocf.io/staff-hours

Need help connecting to the OCF?
    https://ocf.io/ssh

Need to reset your account password?
    https://ocf.io/password"""

jinja_mail_env = Environment(loader=PackageLoader('ocflib', ''))
jinja_mail_env.globals = {
    'mail_signature': MAIL_SIGNATURE,
}


def email_for_user(username, check_exists=True):
    """Return email for a user.

    Currently, just appends @ocf.berkeley.edu, but could eventually do
    something more complicated.
    """
    if check_exists:
        from ocflib.account.search import user_exists
        if not user_exists(username):
            raise ValueError('Account "{}" does not exist.'.format(username))

    return '{}@ocf.berkeley.edu'.format(username)


def send_mail_user(user, subject, body, sender=MAIL_FROM):
    """Send a plan-text mail message to a user."""
    send_mail(email_for_user(user), subject, body, sender=sender)


def send_mail(to, subject, body, *, cc=None, sender=MAIL_FROM):
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
    msg['Cc'] = cc

    # we send the message via sendmail because direct traffic to port 25
    # is firewalled off
    p = subprocess.Popen((SENDMAIL_PATH, '-t', '-oi'),
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
        MAIL_ROOT,
        '[ocflib] Problem report from ' + socket.getfqdn(),
        body,
        sender='ocflib <root@ocf.berkeley.edu>',
    )
