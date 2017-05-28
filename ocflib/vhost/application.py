import re

import requests

VHOST_DB_PATH = '/home/s/st/staff/vhost/vhost-app.conf'
VHOST_DB_URL = 'https://www.ocf.berkeley.edu/~staff/vhost-app.conf'


def get_app_vhost_db():
    """Returns lines from the application vhost database. Loaded from the
    filesystem (if available), or from the web if not."""
    try:
        with open(VHOST_DB_PATH) as f:
            return f.read().splitlines()
    except IOError:
        # fallback to database loaded from web
        return requests.get(VHOST_DB_URL).text.split('\n')


def get_app_vhosts():
    """Returns a list of application virtual hosts in convenient format.

    >>> get_app_vhosts()
    {
    ...
        'ml.berkeley.edu': {
            'username': 'mlab',
            'socket': 'mlab'
            'aliases': [],
            'flags': []
        }
    ...
    }
    """
    def fully_qualify(host):
        """Fully qualifies a hostname (by appending .berkeley.edu) if it's not
        already fully-qualified."""
        return host if '.' in host else host + '.berkeley.edu'

    vhosts = {}

    for line in get_app_vhost_db():
        if not line or line.startswith('#'):
            continue

        fields = line.split(' ')

        if len(fields) < 5:
            flags = []
        else:
            flags = re.match('\[(.*)\]$', fields[4]).group(1).split(',')

        username, host, socket, aliases = fields[:4]

        vhosts[fully_qualify(username if host == '-' else host)] = {
            'username': username,
            'socket': socket if socket != '-' else username,
            'aliases': aliases.split(',') if aliases != '-' else [],
            'flags': flags,
        }

    return vhosts
