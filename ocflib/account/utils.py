"""Random account methods that don't fit anywhere else."""
import grp
import os.path
import re

import pexpect

import ocflib.account.validators as validators
import ocflib.constants as constants


def password_matches(username, password):
    """Returns True if the password matches the user account given"""

    validators.validate_username(username)
    validators.validate_password(username, password, strength_check=False)

    if not validators.user_exists(username):
        raise ValueError("User doesn't exist")

    cmd = 'kinit --no-forwardable -l0 {}@OCF.BERKELEY.EDU'.format(username)
    child = pexpect.spawn(cmd, timeout=10)

    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(username))
    child.sendline(password)

    child.expect(pexpect.EOF)
    child.close()

    return child.exitstatus == 0


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
        raise ValueError('Invalid username')

    return match.group(1)


def home_dir(user):
    """Returns the user's home directory path."""
    return '/' + os.path.join('home', user[0], user[:2], user)


def web_dir(user):
    """Returns the user's web directory path."""
    return '/' + os.path.join('services', 'http', 'users', user[0], user)


def public_html_path(user):
    """Returns the user's public_html path."""
    return os.path.join(home_dir(user), 'public_html')


def is_staff(user, group='ocfstaff'):
    """Return whether the user is a staff member.

    :param group: UNIX group to use to determine if someone is a staff member.
    """
    return user in list_staff(group=group)


def list_staff(group='ocfstaff'):
    """Return a list of staff members.

    :param group: UNIX group to use to determine if someone is a staff member.
    """
    return grp.getgrnam(group).gr_mem


def dn_for_username(username):
    return 'uid={user},{base_people}'.format(
        user=username,
        base_people=constants.OCF_LDAP_PEOPLE,
    )
