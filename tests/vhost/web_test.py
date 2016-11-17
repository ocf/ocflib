import mock
import pytest

from ocflib.account.utils import get_vhost_db
from ocflib.account.utils import get_vhosts
from ocflib.account.utils import has_vhost


VHOSTS_EXAMPLE = """
# [added 2015.05.05 ckuehl]
asucarch archive.asuc.org www.archive.asuc.org,modern.asuc.org,www.modern.asuc.org -

# [added 2015.04.16 ckuehl]
staff! contrib - /contrib [nossl]
ocfwiki docs.ocf.berkeley.edu - - [hsts]
"""  # noqa

VHOSTS_EXAMPLE_PARSED = {
    'archive.asuc.org': {
        'aliases': [
            'www.archive.asuc.org',
            'modern.asuc.org',
            'www.modern.asuc.org',
        ],
        'docroot': '/',
        'flags': [],
        'redirect': None,
        'username': 'asucarch',
    },
    'contrib.berkeley.edu': {
        'aliases': [],
        'docroot': '/contrib',
        'flags': ['nossl'],
        'redirect': '/ https://www.ocf.berkeley.edu/~staff/',
        'username': 'staff',
    },
    'docs.ocf.berkeley.edu': {
        'aliases': [],
        'docroot': '/',
        'flags': ['hsts'],
        'redirect': None,
        'username': 'ocfwiki',
    },
}


@pytest.yield_fixture
def mock_get_vhosts_db():
    with mock.patch(
        'ocflib.vhost.web.get_vhost_db',
        return_value=VHOSTS_EXAMPLE.splitlines()
    ):
        yield


class TestVirtualHosts:

    def test_reads_file_if_exists(self):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            lines = ['hello', 'world']
            mock_open.return_value.__iter__.return_value = lines
            assert get_vhost_db() == lines

    @mock.patch('builtins.open')
    @mock.patch('requests.get')
    def test_reads_web_if_no_file(self, get, mock_open):
        def raise_error(__):
            raise IOError()

        mock_open.side_effect = raise_error
        get.return_value.text = 'hello\nworld'

        assert get_vhost_db() == ['hello', 'world']

    def test_proper_parse(self, mock_get_vhosts_db):
        assert get_vhosts() == VHOSTS_EXAMPLE_PARSED

    @pytest.mark.parametrize('user,should_have_vhost', [
        ('staff', True),
        ('ocfwiki', True),
        ('ckuehl', False),
        ('', False),
    ])
    def test_has_vhost(self, user, should_have_vhost, mock_get_vhosts_db):
        assert has_vhost(user) == should_have_vhost
