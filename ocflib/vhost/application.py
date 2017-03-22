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

    >>> parse_vhosts()
    {
        'ml.berkeley.edu': {
            'username': 'mlab',
            'socket_name': 'mlab'
            'ssl_cert': 'ml.berkeley.edu',
        }
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

        username, host, socket, ssl_cert = fields

        vhosts[fully_qualify(username if host == '-' else host)] = {
            'username': username,
            'socket': socket if socket != '-' else username,
            'ssl_cert': ssl_cert if ssl_cert != '-' else None,
        }

    return vhosts
