"""Methods for figuring out how to identify the current user."""
import os
import pwd
from email.utils import formataddr

from ocflib.misc.mail import email_for_user


def current_uid():
    """Returns numerical UID of current user."""
    return os.getuid()


def current_user():
    """Returns username of current user."""
    return pwd.getpwuid(current_uid()).pw_name


def current_user_fullname():
    """Returns full name (from GECOS, not LDAP) of current user."""
    return pwd.getpwuid(current_uid()).pw_gecos


def current_user_email():
    """Returns @ocf email address of the current user."""
    return email_for_user(current_user())


def current_user_formatted_email():
    """Returns @ocf email address of the current user, including name.

    >>> current_user_formatted_email()
    'Chris Kuehl <ckuehl@ocf.berkeley.edu>'
    """
    return formataddr((current_user_fullname(), current_user_email()))
