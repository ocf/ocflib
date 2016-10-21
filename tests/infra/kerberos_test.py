import subprocess

import mock
import pytest

from ocflib.infra.kerberos import create_kerberos_principal_with_keytab
from ocflib.infra.kerberos import get_kerberos_principal_with_keytab


class TestCreateKerberosPrincipal:

    @mock.patch('pexpect.spawn')
    def test_normal_password(self, mock_spawn):
        mock_spawn.return_value.exitstatus = 0

        create_kerberos_principal_with_keytab(
            'ggroup',
            '/some/keytab',
            'create/admin',
            password='hunter2',
        )

        mock_spawn.assert_called_once_with(
            ('/usr/bin/kadmin -K /some/keytab -p create/admin add ' +
             '--use-defaults ggroup'),
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('hunter2'), mock.call('hunter2')],
        )

    @mock.patch('pexpect.spawn')
    def test_random_password(self, mock_spawn):
        mock_spawn.return_value.exitstatus = 0

        create_kerberos_principal_with_keytab(
            'ggroup',
            '/some/keytab',
            'create/admin',
        )

        mock_spawn.assert_called_once_with(
            ('/usr/bin/kadmin -K /some/keytab -p create/admin add ' +
             '--use-defaults ggroup'),
            timeout=10,
        )
        assert len(mock_spawn.return_value.sendline.call_args[0][0]) == 100

    @mock.patch('pexpect.spawn')
    def test_errors(self, mock_spawn):
        mock_spawn.return_value.before.decode.return_value = (
            'kadmin: kadm5_create_principal: Principal already exists'
        )
        mock_spawn.return_value.exitstatus = 1

        with pytest.raises(ValueError):
            create_kerberos_principal_with_keytab(
                'ggroup',
                '/some/keytab',
                'create/admin',
            )


class TestGetKerberosPrincipal:

    @mock.patch('subprocess.check_output')
    def test_existing_principal(self, mock_check_output):
        assert get_kerberos_principal_with_keytab(
            'ggroup',
            '/some/keytab',
            'create/admin',
        )

        mock_check_output.assert_called_once_with(
            '/usr/bin/kadmin -K /some/keytab -p create/admin get ggroup',
            timeout=10,
        )

    @mock.patch('subprocess.check_output')
    def test_nonexistent_principal(self, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(
            1,
            '/usr/bin/kadmin -K /some/keytab -p create/admin get ggroup',
            'kadmin: get ggroup: Principal does not exist',
        )

        assert not get_kerberos_principal_with_keytab(
            'ggroup',
            '/some/keytab',
            'create/admin',
        )

    @mock.patch('subprocess.check_output')
    def test_error(self, mock_check_output):
        mock_check_output.side_effect = subprocess.CalledProcessError(
            1,
            '/usr/bin/kadmin -K /some/keytab -p create/admin get ggroup',
            'kadmin: get ggroup: no such file or directory'
        )

        with pytest.raises(ValueError):
            get_kerberos_principal_with_keytab(
                'ggroup',
                '/some/keytab',
                'create/admin',
            )
