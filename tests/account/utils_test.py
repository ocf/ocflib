import mock
import pexpect
import pytest

from ocflib.account.utils import dn_for_username
from ocflib.account.utils import extract_username_from_principal
from ocflib.account.utils import get_vhost_db
from ocflib.account.utils import get_vhosts
from ocflib.account.utils import has_vhost
from ocflib.account.utils import home_dir
from ocflib.account.utils import is_staff
from ocflib.account.utils import list_staff
from ocflib.account.utils import password_matches
from ocflib.account.utils import web_dir


class TestPasswordMatches:

    @pytest.mark.parametrize('user', [
        '',
        '; rm -rf /',
        ';',
        '&&',
        ';exit',
        '\\',
        'thisistoolong',
    ])
    def test_fails_with_bad_username(self, user):
        with pytest.raises(ValueError):
            password_matches(user, 'hunter2')

    @pytest.mark.parametrize('password', [
        'asdf\nasdf',
        '\n\n\n\n\n\n',
        'a\0asdf',
    ])
    def test_fails_with_bad_password(self, password):
        with pytest.raises(ValueError):
            password_matches('ckuehl', password)

    @mock.patch('ocflib.account.validators.user_exists', return_value=False)
    def test_fails_if_user_does_not_exist(self, __):
        with pytest.raises(ValueError):
            password_matches('ckuehl', 'hunter2')

    @mock.patch('ocflib.account.validators.user_exists', return_value=True)
    @mock.patch('pexpect.spawn')
    def test_calls_pexpect_correctly(self, spawn, __):
        password_matches('ckuehl', 'hunter2')
        spawn.assert_called_with(
            'kinit --no-forwardable -l0 ckuehl@OCF.BERKELEY.EDU',
            timeout=10,
        )

        child = spawn.return_value

        assert child.expect.mock_calls == [
            mock.call.first('ckuehl@OCF.BERKELEY.EDU\'s Password:'),
            mock.call.second(pexpect.EOF),
        ]
        child.sendline.assert_called_with('hunter2')
        assert child.close.called

    @mock.patch('ocflib.account.validators.user_exists', return_value=True)
    @mock.patch('pexpect.spawn')
    @pytest.mark.parametrize('exitstatus,success', [
        (0, True),

        # this is excessive, but we want to be really sure we don't
        # accidentally accept a bad password
        (1, False),
        (22, False),
        (-1, False),
        (None, False),
    ])
    def test_returns_correctly(self, spawn, __, exitstatus, success):
        spawn.return_value.exitstatus = exitstatus
        assert password_matches('ckuehl', 'hunter2') == success


class TestExtractUsernameFromPrincipal:

    @pytest.mark.parametrize('principal,username', [
        ('ckuehl@OCF.BERKELEY.EDU', 'ckuehl'),
        ('ckuehl/admin@OCF.BERKELEY.EDU', 'ckuehl'),
        ('ckuehl/root@OCF.BERKELEY.EDU', 'ckuehl'),
    ])
    def test_success(self, principal, username):
        assert extract_username_from_principal(principal) == username

    @pytest.mark.parametrize('principal', [
        '',
        'ckuehl',
        'ckuehl@ocf.berkeley.edu',
        '@OCF.BERKELEY.EDU',
        '@',
        'thisiswaytoolongn@OCF.BERKELEY.EDU',
        'ckuehl+root@OCF.BERKELEY.EDU',
    ])
    def test_fails_on_bad_input(self, principal):
        with pytest.raises(ValueError):
            extract_username_from_principal(principal)


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
        'ocflib.account.utils.get_vhost_db',
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


class TestUserPaths:

    @pytest.mark.parametrize('user,expected', [
        ('ckuehl', '/home/c/ck/ckuehl'),
        ('ggroup', '/home/g/gg/ggroup'),
    ])
    def test_home_dir(self, user, expected):
        assert home_dir(user) == expected

    @pytest.mark.xfail
    @pytest.mark.parametrize('user', [
        '',
        'c',
        'ck',
    ])
    def test_home_dir_errors_bad_user(self, user):
        with pytest.raises(ValueError):
            home_dir(user)

    @pytest.mark.parametrize('user,expected', [
        ('ckuehl', '/services/http/users/c/ckuehl'),
        ('ggroup', '/services/http/users/g/ggroup'),
    ])
    def test_web_dir(self, user, expected):
        assert web_dir(user) == expected

    @pytest.mark.xfail
    @pytest.mark.parametrize('user', [
        '',
        'c',
        'ck',
    ])
    def test_web_dir_errors_bad_user(self, user):
        with pytest.raises(ValueError):
            web_dir(user)


@pytest.mark.parametrize('user,group,expected', [
    ('ckuehl', None, True),
    ('ckuehl', 'ocfroot', True),
    ('bpreview', None, False),
    ('bpreview', 'ocfroot', False),
])
def test_is_staff(user, group, expected):
    kwargs = {} if not group else {'group': group}
    assert is_staff(user, **kwargs) is expected


def test_list_staff():
    staff = list_staff()
    assert 'ckuehl' in staff
    assert 'bpreview' not in staff
    assert 5 <= len(staff) <= 75


def test_dn_for_username():
    assert (dn_for_username('kpengboy') ==
            'uid=kpengboy,ou=People,dc=OCF,dc=Berkeley,dc=EDU')
