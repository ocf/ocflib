import mock
import pytest

from ocflib.account.validators import user_exists
from ocflib.account.validators import username_reserved
from ocflib.account.validators import validate_password
from ocflib.account.validators import validate_username


class TestValidateUsername:

    @pytest.mark.parametrize('username', [
        # reserved
        'ocfdeploy',
        'ocf',
        'ocfrocks',
        'www-data',
        'root',

        # bad length
        'a',
        '',
        'hellooooooooooooo',

        # bad characters
        'Ckuehl',
        'ckuehl!',
        '123123',
        'f00f00',
    ])
    def test_failure(self, username):
        with pytest.raises(ValueError):
            validate_username(username, check_exists=True)

    def test_failure_nonexist(self):
        """Test that it fails with a nonexistent username.

        We can't just use "nonexist" since this is also a reserved username. We
        need mocking to avoid flakiness if somebody registers that account.
        """
        with mock.patch('ocflib.account.validators.user_exists', return_value=False) as m, \
                pytest.raises(ValueError):
            validate_username('asdf', check_exists=True)
        m.assert_called_once_with('asdf')

    @pytest.mark.parametrize('username', ['ckuehl', 'daradib'])
    def test_success(fail, username):
        validate_username(username, check_exists=True)


class TestValidatePassword:

    @pytest.mark.parametrize('password', [
        # too short
        'hunter2',

        # too similar to username
        'ckuehlckuehl',

        # too simple (cracklib)
        'aaaaaaa',
        'hellohello',
        '12345678',

        # tabs or newlines
        'a really strong password\tbut with tab',
        'a really strong password\nbut with newline',
    ])
    def test_failure(self, password):
        with pytest.raises(ValueError):
            validate_password('ckuehl', password)

    @pytest.mark.parametrize('password', ['a strong password', '53y4kZ1hKq'])
    def test_success(self, password):
        validate_password('ckuehl', password)


class TestUserExists:

    @pytest.mark.parametrize('username', ['nonexist', 'ocfrocks'])
    def test_not_exists(self, username):
        assert not user_exists(username)

    @pytest.mark.parametrize('username', ['ckuehl', 'staff', 'root', 'sshd'])
    def test_exists(self, username):
        assert user_exists(username)


class TestUsernameReserved:

    @pytest.mark.parametrize('username', [
        # starts with ocf
        'ocf',
        'ocfrocks',

        # in the list
        'jenkins',
        'puppet',
    ])
    def test_reserved(self, username):
        assert username_reserved(username)

    @pytest.mark.parametrize('username', ['ckuehl', 'ggroup'])
    def test_not_reserved(self, username):
        assert not username_reserved(username)

    def test_checks_etc_passwd(self):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            lines = [
                'root:x:0:0:root:/root:/bin/bash',
                'somename:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin',
            ]

            mock_open.return_value.__iter__.return_value = lines

            with mock.patch('ocflib.misc.mail.send_problem_report') \
                    as send_report:
                assert username_reserved('somename')
                assert send_report.called
