import mock

from ocflib.vhost.application import get_app_vhosts


VHOSTS_EXAMPLE = """
asucapp api.asuc.ocf.berkeley.edu prod api.asuc.ocf.berkeley.edu
ggroup dev-app.ocf.berkeley.edu - -
upe - - -
"""

VHOSTS_EXAMPLE_PARSED = {
    'api.asuc.ocf.berkeley.edu': {
        'socket': 'prod',
        'ssl_cert': 'api.asuc.ocf.berkeley.edu',
        'username': 'asucapp',
    },
    'dev-app.ocf.berkeley.edu': {
        'socket': 'ggroup',
        'ssl_cert': None,
        'username': 'ggroup',
    },
    'upe.berkeley.edu': {
        'socket': 'upe',
        'ssl_cert': None,
        'username': 'upe',
    },
}


class TestVirtualHosts:

    # The database-reading function is identical to that in vhost.web, so
    # there's not much meaning in making tests slower by testing them.

    @mock.patch(
        'ocflib.vhost.application.get_app_vhost_db',
        return_value=VHOSTS_EXAMPLE.splitlines(),
    )
    def test_proper_parse(self, mock_get_app_vhost_db):
        assert get_app_vhosts() == VHOSTS_EXAMPLE_PARSED
