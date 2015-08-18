from base64 import b64encode

import mock
import pytest

from ocflib.infra.ldap import create_ldap_entry_with_keytab


@pytest.yield_fixture
def mock_spawn():
    with mock.patch('pexpect.spawn') as spawn:
        yield spawn


@pytest.yield_fixture
def mock_send_problem_report():
    with mock.patch('ocflib.infra.ldap.send_problem_report') as m:
        yield m


class TestCreateLdapEntry:

    def test_normal_creation(self, mock_spawn, mock_send_problem_report):
        mock_spawn.return_value.before = b'\n'
        create_ldap_entry_with_keytab(
            'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ['b', 'c'], 'd': ['e']},
            '/nonexist',
            'create/admin',
        )

        mock_spawn.assert_called_with(
            'kinit -t /nonexist create/admin ldapadd',
            timeout=10,
        )
        mock_spawn.return_value.expect.assert_has_calls([
            mock.call('SASL data security layer installed.'),
            mock.call('adding new entry "uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU"'),
        ])

        def encode(attr, value):
            return '{attr}:: {value}'.format(
                attr=attr,
                value=b64encode(value.encode('utf8')).decode('ascii'),
            )

        mock_spawn.return_value.sendline.assert_has_calls([
            mock.call(encode(attr, value))
            for attr, value in [
                ('dn', 'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU'),
                ('a', 'b'),
                ('a', 'c'),
                ('d', 'e'),
            ]
        ], any_order=True)
        assert mock_spawn.return_value.sendeof.called
        assert not mock_send_problem_report.called

    def test_already_exists(self, mock_spawn, mock_send_problem_report):
        mock_spawn.return_value.before = b'\nAlready exists (68)\n'
        with pytest.raises(ValueError):
            create_ldap_entry_with_keytab(
                'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'a': ['b', 'c'], 'd': ['e']},
                '/nonexist',
                'create/admin',
            )
        assert not mock_send_problem_report.called

    def test_unexpected_error(self, mock_spawn, mock_send_problem_report):
        mock_spawn.return_value.before = b'\nlol wut is this error\n'
        with pytest.raises(ValueError):
            create_ldap_entry_with_keytab(
                'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'a': ['b', 'c'], 'd': ['e']},
                '/nonexist',
                'create/admin',
            )
        assert mock_send_problem_report.called
