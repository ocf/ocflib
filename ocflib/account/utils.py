"""Random account methods that don't fit anywhere else."""
import grp
import os.path
import re
import subprocess

import pexpect

import ocflib.account.validators as validators
from ocflib.infra.ldap import OCF_LDAP_PEOPLE
import ocflib.misc.krb5

LDAP_MAIL_ATTR = 'mail'


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

    REGEX = '^([a-z]{3,16})(/[a-z]*)?@OCF\\.BERKELEY\\.EDU$'
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


def is_in_group(user, group):
    """Return whether the user is in a group.

    Only will return True if the user is a supplementary member, so "sorry"
    won't work here.

    :param group: UNIX group to use.
    """
    return user in list_group(group)


def list_group(group):
    """Return a list of OCF users in a group

    Only returns users who have this group listed as a supplementary group, so
    "sorry" won't work here.

    :param group: UNIX group to list.
    """
    return grp.getgrnam(group).gr_mem


def dn_for_username(username):
    return 'uid={user},{base_people}'.format(
        user=username,
        base_people=OCF_LDAP_PEOPLE,
    )


def get_email(username, have_ticket=True, operatorname=""):
    """Returns current email, or None."""
    """Assume a ticket is created already, otherwise this'd require username and help you do that"""

    if not have_ticket:
        if operatorname == "":
            # Or do you want this to just automatically be current user?
            raise ValueError("Operator username must not be empty.")
        ocflib.misc.krb5.kerberos_init(operatorname)

    # Since the mail attribute is private, and we can't get the attribute's
    # value without authenticating, we have to use ldapsearch here instead of
    # something like ldap3.
    output = subprocess.check_output(
        ('ldapsearch', '-LLL', 'uid={}'.format(username), LDAP_MAIL_ATTR),
        stderr=subprocess.DEVNULL,
    ).decode('utf-8').split('\n')

    if not have_ticket:
        ocflib.misc.krb5.kerberos_destroy()

    mail_attr = [attr for attr in output if attr.startswith(LDAP_MAIL_ATTR + ': ')]

    if mail_attr:
        # Strip the '{LDAP_MAIL_ATTR}: ' from the beginning of the string
        return mail_attr[0][len(LDAP_MAIL_ATTR) + 2:].strip()
