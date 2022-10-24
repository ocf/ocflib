import mock
import pexpect
import pytest

from ocflib.account.utils import dn_for_username
from ocflib.account.utils import extract_username_from_principal
from ocflib.account.utils import home_dir
from ocflib.account.utils import is_in_group
from ocflib.account.utils import list_group
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
    ('gstaff', 'ocfstaff', True),
    ('guser', 'ocfstaff', False),
    ('testopstaff', 'opstaff', True),
    ('guser', 'opstaff', False),
])
def test_is_in_group(user, group, expected):
    assert is_in_group(user, group) is expected


def test_list_group():
    ocfstaff = list_group('ocfstaff')
    assert 'gstaff' in ocfstaff
    assert 'guser' not in ocfstaff
    assert 5 <= len(ocfstaff) <= 500

    opstaff = list_group('opstaff')
    assert 'testopstaff' in opstaff
    assert 'guser' not in opstaff
    assert 1 <= len(opstaff) <= 30

    assert len(list_group('ocfroot')) >= 1


def test_dn_for_username():
    assert (dn_for_username('kpengboy') ==
            'uid=kpengboy,ou=People,dc=OCF,dc=Berkeley,dc=EDU')
