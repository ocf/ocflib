import mock
import pytest

from ocflib.vhost.web import eligible_for_vhost
from ocflib.vhost.web import get_vhost_db
from ocflib.vhost.web import get_vhosts
from ocflib.vhost.web import has_vhost


VHOSTS_EXAMPLE = """
# [added 2015.05.05 ckuehl]
asucarch archive.asuc.org www.archive.asuc.org,modern.asuc.org,www.modern.asuc.org -

# [added 2015.04.16 ckuehl]
staff contrib - /contrib [nossl]
ocfwiki docs.ocf.berkeley.edu - - [hsts]
"""

VHOSTS_EXAMPLE_PARSED = {
    'archive.asuc.org': {
        'aliases': [
            'www.archive.asuc.org',
            'modern.asuc.org',
            'www.modern.asuc.org',
        ],
        'docroot': '/',
        'flags': [],
        'username': 'asucarch',
    },
    'contrib.berkeley.edu': {
        'aliases': [],
        'docroot': '/contrib',
        'flags': ['nossl'],
        'username': 'staff',
    },
    'docs.ocf.berkeley.edu': {
        'aliases': [],
        'docroot': '/',
        'flags': ['hsts'],
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
            text = 'hello\nworld\n'
            mock_open.return_value.read.return_value = text
            assert get_vhost_db() == text.splitlines()

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

    @pytest.mark.parametrize('user,should_be_eligible', [
        ('mattmcal', False),
        ('ggroup', True),
        ('bh', True),
    ])
    def test_eligible_for_vhost(self, user, should_be_eligible):
        assert eligible_for_vhost(user) == should_be_eligible
