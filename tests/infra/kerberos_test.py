import mock
import pytest

from ocflib.infra.kerberos import create_kerberos_principal_with_keytab


@pytest.yield_fixture
def mock_spawn():
    with mock.patch('pexpect.spawn') as spawn:
        yield spawn


class TestCreateKerberosPrincipal:

    def test_normal_password(self, mock_spawn):
        create_kerberos_principal_with_keytab(
            'ggroup',
            '/some/keytab',
            'create/admin',
            password='hunter2',
        )

        mock_spawn.assert_called_with(
            ('/usr/bin/kadmin -K /some/keytab -p create/admin add ' +
             '--use-defaults ggroup'),
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('hunter2'), mock.call('hunter2')],
        )

    def test_random_password(self, mock_spawn):
        create_kerberos_principal_with_keytab(
            'ggroup',
            '/some/keytab',
            'create/admin',
        )

        mock_spawn.assert_called_with(
            ('/usr/bin/kadmin -K /some/keytab -p create/admin add ' +
             '--use-defaults ggroup'),
            timeout=10,
        )
        assert len(mock_spawn.return_value.sendline.call_args[0][0]) == 100

    def test_errors(self, mock_spawn):
        mock_spawn.return_value.before.decode.return_value = (
            'kadmin: kadm5_create_principal: Principal already exists'
        )

        with pytest.raises(ValueError):
            create_kerberos_principal_with_keytab(
                'ggroup',
                '/some/keytab',
                'create/admin',
            )
