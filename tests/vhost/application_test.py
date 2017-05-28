import mock

from ocflib.vhost.application import get_app_vhosts


VHOSTS_EXAMPLE = """
asucapp api.asuc.ocf.berkeley.edu prod api.asuc.org
ggroup dev-app.ocf.berkeley.edu - -
upe - - -
"""

VHOSTS_EXAMPLE_PARSED = {
    'api.asuc.ocf.berkeley.edu': {
        'socket': 'prod',
        'aliases': ['api.asuc.org'],
        'username': 'asucapp',
        'flags': [],
    },
    'dev-app.ocf.berkeley.edu': {
        'socket': 'ggroup',
        'aliases': [],
        'username': 'ggroup',
        'flags': [],
    },
    'upe.berkeley.edu': {
        'socket': 'upe',
        'aliases': [],
        'username': 'upe',
        'flags': [],
    },
}


class TestVirtualHosts:

    # The database-reading function is identical to that in vhost.web, so
    # there's not much meaning in making tests slower by testing it.

    @mock.patch(
        'ocflib.vhost.application.get_app_vhost_db',
        return_value=VHOSTS_EXAMPLE.splitlines(),
    )
    def test_proper_parse(self, mock_get_app_vhost_db):
        assert get_app_vhosts() == VHOSTS_EXAMPLE_PARSED
