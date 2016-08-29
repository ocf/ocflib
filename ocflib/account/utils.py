"""Random account methods that don't fit anywhere else."""
import grp
import os.path
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


def get_vhost_db():
    """Returns lines from the vhost database. Loaded from the filesystem (if
    available), or from the web if not."""
    try:
        with open(constants.VHOST_DB_PATH) as f:
            return list(map(str.strip, f))
    except IOError:
        # fallback to database loaded from web
        return requests.get(constants.VHOST_DB_URL).text.split('\n')


def get_vhosts():
    """Returns a list of virtual hosts in convenient format.

    >>> parse_vhosts()
    {
        'bpreview.berkeley.edu': {
            'username': 'bpr',
            'aliases': ['bpr.berkeley.edu'],
            'docroot': '/',
            'redirect': None  # format is '/ https://some.other.site/'
        }
    }
    """
    def fully_qualify(host):
        """Fully qualifies a hostname (by appending .berkeley.edu) if it's not
        already fully-qualified."""
        return host if '.' in host else host + '.berkeley.edu'

    vhosts = {}

    for line in get_vhost_db():
        if not line or line.startswith('#'):
            continue

        fields = line.split(' ')

        if len(fields) < 5:
            flags = []
        else:
            flags = re.search('^\[(.*)\]$', fields[4]).group(1).split(',')

        username, host, aliases, docroot = fields[:4]

        redirect = None

        if username.endswith('!'):
            username = username[:-1]
            redirect = '/ https://www.ocf.berkeley.edu/~{}/'.format(username)

        if aliases != '-':
            aliases = list(map(fully_qualify, aliases.split(',')))
        else:
            aliases = []

        vhosts[fully_qualify(username if host == '-' else host)] = {
            'username': username,
            'aliases': aliases,
            'docroot': '/' if docroot == '-' else docroot,
            'redirect': redirect,
            'flags': flags
        }

    return vhosts


def has_vhost(user):
    """Returns whether or not a virtual host is already configured for
    the given user."""
    return any(vhost['username'] == user for vhost in get_vhosts().values())


def home_dir(user):
    """Returns the user's home directory path."""
    return '/' + os.path.join('home', user[0], user[:2], user)


def web_dir(user):
    """Returns the user's web directory path."""
    return '/' + os.path.join('services', 'http', 'users', user[0], user)


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
