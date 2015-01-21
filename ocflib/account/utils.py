"""Random account methods that don't fit anywhere else."""
import pexpect
import requests

import ocflib.account.validators as validators
import ocflib.constants as constants


def password_matches(username, password):
    """Returns True if the password matches the user account given"""

    validators.validate_username(username)
    validators.validate_password(username, password, strength_check=False)

    if not validators.user_exists(username):
        raise Exception("User doesn't exist")

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
    line_matches = lambda fields: len(fields) > 0 and fields[0] in check

    vhosts = requests.get(constants.VHOST_DB_URL).text.split("\n")
    return any(line_matches(line.split()) for line in vhosts)
