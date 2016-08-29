from base64 import b64encode

import mock
import pytest

from ocflib.infra.ldap import create_ldap_entry_with_keytab
from ocflib.infra.ldap import modify_ldap_entry_with_keytab


def encode(attr, value):
    return '{attr}:: {value}'.format(
        attr=attr,
        value=b64encode(value.encode('utf8')).decode('ascii'),
    )


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
            'kinit -t /nonexist create/admin ldapmodify',
            timeout=10,
        )
        mock_spawn.return_value.expect.assert_has_calls([
            mock.call('SASL data security layer installed.'),
            mock.call('entry "uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU"'),
        ])

        mock_spawn.return_value.sendline.assert_has_calls([
            mock.call(encode(attr, value))
            for attr, value in [
                ('dn', 'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU'),
                ('a', 'b'),
                ('a', 'c'),
                ('d', 'e'),
            ]
        ] + [mock.call('changetype: add')], any_order=True)
        assert mock_spawn.return_value.sendeof.called
        assert not mock_send_problem_report.called

    def test_create_existing(self, mock_spawn, mock_send_problem_report):
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


class TestModifyLdapEntry:

    def test_normal_modification(self, mock_spawn, mock_send_problem_report):
        mock_spawn.return_value.before = b'\n'
        modify_ldap_entry_with_keytab(
            'uid=mattmcal,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ['b', 'c'], 'calnetUid': ['1234']},
            '/nonexist',
            'create/admin'
        )

        mock_spawn.assert_called_with(
            'kinit -t /nonexist create/admin ldapmodify',
            timeout=10,
        )
        mock_spawn.return_value.expect.assert_has_calls([
            mock.call('SASL data security layer installed.'),
            mock.call('entry "uid=mattmcal,ou=People,dc=OCF,dc=Berkeley,dc=EDU"'),
        ])

        mock_spawn.return_value.sendline.assert_has_calls((
            mock.call(encode('dn', 'uid=mattmcal,ou=People,dc=OCF,dc=Berkeley,dc=EDU')),
            mock.call('changetype: modify'),
            mock.call('replace: a'),
            mock.call(encode('a', 'b')),
            mock.call(encode('a', 'c')),
            mock.call('-'),
            mock.call('replace: calnetUid'),
            mock.call(encode('calnetUid', '1234')),
        ), any_order=True)
        assert mock_spawn.return_value.sendeof.called
        assert not mock_send_problem_report.called

    def test_modify_nonexistent(self, mock_spawn, mock_send_problem_report):
        mock_spawn.return_value.before = b'\nNo such object (32)\n'
        with pytest.raises(ValueError):
            modify_ldap_entry_with_keytab(
                'uid=unknown,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'a': ['b', 'c'], 'd': ['e']},
                '/nonexist',
                'create/admin'
            )
        assert not mock_send_problem_report.called
