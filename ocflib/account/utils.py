"""Random account methods that don't fit anywhere else."""
import re

import pexpect
import requests

import ocflib.account.validators as validators
import ocflib.constants as constants


def password_matches(username, password):
    """Returns True if the password matches the user account given"""

    validators.validate_username(username)
    validators.validate_password(username, password, strength_check=False)

    if not validators.user_exists(username):
        raise ValueError("User doesn't exist")

    cmd = "kinit --no-forwardable -l0 {}@OCF.BERKELEY.EDU".format(username)
    child = pexpect.spawn(cmd, timeout=10)

    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(username))
    child.sendline(password)

    child.expect(pexpect.EOF)
    child.close()

    return child.exitstatus == 0


def has_vhost(user):
    """Returns whether or not a virtual host is already configured for
    the given user."""

    check = (user, user + "!")

    def line_matches(fields):
        return len(fields) > 0 and fields[0] in check

    vhosts = requests.get(constants.VHOST_DB_URL).text.split("\n")
    return any(line_matches(line.split()) for line in vhosts)


def extract_username_from_principal(principal):
    """Extract username from principal.

    >>> extract_username("ckuehl@OCF.BERKELEY.EDU")
    'ckuehl'

    >>> extract_username("ckuehl/admin@OCF.BERKELEY.EDU")
    'ckuehl'
    """

    REGEX = '^([a-z]{3,8})(/[a-z]*)?@OCF\\.BERKELEY\\.EDU$'
    match = re.match(REGEX, principal)

    if not match:
        raise ValueError("Invalid username")

    return match.group(1)
