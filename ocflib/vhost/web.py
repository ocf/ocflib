import re

import requests

from ocflib import constants


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
