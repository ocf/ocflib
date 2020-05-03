import re

VHOST_DB_PATH = '/etc/ocf/vhost-app.conf'


def get_app_vhost_db():
    """Returns lines from the application vhost config file."""
    with open(VHOST_DB_PATH) as f:
        return f.read().splitlines()


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
            flags = re.match(r'\[(.*)\]$', fields[4]).group(1).split(',')

        username, host, socket, aliases = fields[:4]

        vhosts[fully_qualify(username if host == '-' else host)] = {
            'username': username,
            'socket': socket if socket != '-' else username,
            'aliases': aliases.split(',') if aliases != '-' else [],
            'flags': flags,
        }

    return vhosts
