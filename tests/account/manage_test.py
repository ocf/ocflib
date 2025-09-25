import mock
import pytest

from ocflib.account.manage import _notify_password_change
from ocflib.account.manage import change_password_with_keytab
from ocflib.account.manage import change_password_with_staffer
from ocflib.account.manage import modify_ldap_attributes


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


@pytest.yield_fixture
def mock_modify_ldap_entry():
    with mock.patch(
        'ocflib.infra.ldap.modify_ldap_entry',
    ) as modify_ldap_entry:
        yield modify_ldap_entry


class TestChangePasswordWithStaffer:

    def _chpass(self, mock_spawn):
        change_password_with_staffer(
            'ggroup',
            'strong_hunter237128763',
            'ckuehl/admin',
            'super_hunter237128763',
        )
        mock_spawn.assert_called_with(
            '/usr/bin/kadmin -p ckuehl/admin cpw ggroup',
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('strong_hunter237128763'), mock.call('strong_hunter237128763')],
        )

    def test_success(self, mock_spawn, mock_notify_password_change):
        self._chpass(mock_spawn)
        mock_notify_password_change.assert_called_once_with('ggroup', comment=None)

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
            'strong_hunter237128763',
            '/some/keytab',
            'create/admin',
        )
        mock_spawn.assert_called_with(
            '/usr/bin/kadmin -K /some/keytab -p create/admin cpw ggroup',
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('strong_hunter237128763'), mock.call('strong_hunter237128763')],
        )

    def test_success(self, mock_spawn, mock_notify_password_change):
        self._chpass(mock_spawn)
        mock_notify_password_change.assert_called_once_with('ggroup', comment=None)

    def test_kadmin_failure(self, mock_spawn, mock_notify_password_change):
        mock_spawn.return_value.before.decode.return_value = (
            'kadmin: cpw ggroup: Looping detected inside krb5_get_in_tkt'
        )
        with pytest.raises(ValueError):
            self._chpass(mock_spawn)
        assert not mock_notify_password_change.called


class TestModifyLdapAttributes:

    def test_success(self, mock_modify_ldap_entry):
        modify_ldap_attributes(
            'ggroup',
            {'a': ('b', 'c'), 'loginShell': '/bin/bash'},
            keytab='/some/keytab',
            admin_principal='create/admin',
        )
        mock_modify_ldap_entry.assert_called_once_with(
            'uid=ggroup,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ('b', 'c'), 'loginShell': '/bin/bash'},
            keytab='/some/keytab',
            admin_principal='create/admin',
        )

    @pytest.mark.parametrize('attrs', [
        {'loginShell': '/bin/bush'},
        {'loginShell': ''},
    ])
    def test_invalid_attributes(self, attrs, mock_modify_ldap_entry):
        with pytest.raises(ValueError):
            modify_ldap_attributes(
                'ggroup',
                attrs,
                keytab='/some/keytab',
                admin_principal='create/admin',
            )
        assert not mock_modify_ldap_entry.called


class TestNotifyPasswordChange:

    @mock.patch('ocflib.misc.mail.send_mail_user')
    def test_without_comment(self, mock_send_mail_user):
        _notify_password_change('ckuehl')
        mock_send_mail_user.assert_called_once_with('ckuehl', mock.ANY, mock.ANY)

    @mock.patch('ocflib.misc.mail.send_mail_user')
    def test_with_comment(self, mock_send_mail_user):
        _notify_password_change('ckuehl', comment='HERPDERP')
        mock_send_mail_user.assert_called_once_with('ckuehl', mock.ANY, mock.ANY)
        assert '\nHERPDERP\n' in mock_send_mail_user.call_args_list[0][0][2]
