import mock
import pytest

from ocflib.account.manage import _notify_password_change
from ocflib.account.manage import change_password_with_keytab
from ocflib.account.manage import change_password_with_staffer


@pytest.yield_fixture
def mock_spawn():
    with mock.patch('pexpect.spawn') as spawn:
        yield spawn


@pytest.yield_fixture
def mock_notify_password_change():
    with mock.patch(
        'ocflib.account.manage._notify_password_change',
    ) as _notify_password_change:
        yield _notify_password_change


class TestChangePasswordWithStaffer:

    def _chpass(self, mock_spawn):
        change_password_with_staffer(
            'ggroup',
            'strong_hunter2',
            'ckuehl/admin',
            'super_hunter2',
        )
        mock_spawn.assert_called_with(
            '/usr/bin/kadmin -p ckuehl/admin cpw ggroup',
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('strong_hunter2'), mock.call('strong_hunter2')],
        )

    def test_success(self, mock_spawn, mock_notify_password_change):
        self._chpass(mock_spawn)
        mock_notify_password_change.assert_called_once_with('ggroup')

    @pytest.mark.parametrize('error', [
        'kadmin: cpw ggroup: Looping detected inside krb5_get_in_tkt',
        'kadmin: some random error you do not expect',
    ])
    def test_kadmin_failure(
        self,
        error,
        mock_spawn,
        mock_notify_password_change,
    ):
        mock_spawn.return_value.before.decode.return_value = error
        with pytest.raises(ValueError):
            self._chpass(mock_spawn)
        assert not mock_notify_password_change.called


class TestChangePasswordWithKeytab:

    def _chpass(self, mock_spawn):
        change_password_with_keytab(
            'ggroup',
            'strong_hunter2',
            '/some/keytab',
            'create/admin',
        )
        mock_spawn.assert_called_with(
            '/usr/bin/kadmin -K /some/keytab -p create/admin cpw ggroup',
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('strong_hunter2'), mock.call('strong_hunter2')],
        )

    def test_success(self, mock_spawn, mock_notify_password_change):
        self._chpass(mock_spawn)
        mock_notify_password_change.assert_called_once_with('ggroup')

    def test_kadmin_failure(self, mock_spawn, mock_notify_password_change):
        mock_spawn.return_value.before.decode.return_value = (
            'kadmin: cpw ggroup: Looping detected inside krb5_get_in_tkt'
        )
        with pytest.raises(ValueError):
            self._chpass(mock_spawn)
        assert not mock_notify_password_change.called


@mock.patch('ocflib.misc.mail.send_mail_user')
def test_notify_password_change(mock_send_mail_user):
    _notify_password_change('ckuehl')
    mock_send_mail_user.assert_called_once_with('ckuehl', mock.ANY, mock.ANY)
