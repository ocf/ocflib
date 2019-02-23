import mock
import pytest

from ocflib.vhost.web import eligible_for_vhost
from ocflib.vhost.web import get_vhost_db
from ocflib.vhost.web import get_vhosts
from ocflib.vhost.web import has_vhost


VHOSTS_EXAMPLE = """
# added 2017-09-16 kpengboy
staff ofc - /ofc

# [added 2015.05.05 ckuehl]
asucarch archive.asuc.org www.archive.asuc.org,modern.asuc.org,www.modern.asuc.org -

# [added 2015.04.16 ckuehl]
ocfwiki docs.ocf.berkeley.edu - - [hsts]
"""

VHOSTS_EXAMPLE_PARSED = {
    'ofc.berkeley.edu': {
        'aliases': [],
        'docroot': '/ofc',
        'flags': [],
        'username': 'staff',
    },
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


@pytest.yield_fixture
def mock_group_user_attrs():
    with mock.patch(
        'ocflib.vhost.web.user_attrs',
        return_value={'callinkOid': ['0']}
    ):
        yield


@pytest.yield_fixture
def mock_staff_ucb_attrs():
    with mock.patch(
        'ocflib.vhost.web.user_attrs_ucb',
        return_value={'berkeleyEduAffiliations': ['EMPLOYEE-TYPE-ACADEMIC']}
    ):
        with mock.patch(
            'ocflib.vhost.web.user_attrs',
            return_value={'calnetUid': ['0']}
        ):
            yield


@pytest.yield_fixture
def mock_user_attrs_uneligible():
    with mock.patch(
        'ocflib.vhost.web.user_attrs_ucb',
        return_value=None
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

    @pytest.mark.usefixtures('mock_group_user_attrs')
    def test_groups_eligible_for_vhost(self):
        assert eligible_for_vhost('ggroups')

    @pytest.mark.usefixtures('mock_staff_ucb_attrs')
    def test_staff_eligible_for_vhost(self):
        assert eligible_for_vhost('bh')

    @pytest.mark.usefixtures('mock_user_attrs_uneligible')
    def test_not_eligible_for_vhost(self):
        assert not eligible_for_vhost('mattmcal')
