from datetime import datetime
from datetime import timedelta
from datetime import timezone
from subprocess import CalledProcessError
from textwrap import dedent

import mock
import pytest

from ocflib.infra.ldap import create_ldap_entry
from ocflib.infra.ldap import modify_ldap_entry


@pytest.yield_fixture
def mock_subprocess_check_output():
    with mock.patch('subprocess.check_output') as check_output:
        yield check_output


@pytest.yield_fixture
def mock_send_problem_report():
    with mock.patch('ocflib.infra.ldap.send_problem_report') as m:
        yield m


class TestCreateLdapEntry:

    def test_normal_creation(self, mock_subprocess_check_output, mock_send_problem_report):
        create_ldap_entry(
            'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ['b', 'c']},
        )

        # These are the base64-encoded versions of the attributes above
        ldif = dedent("""
            dn:: dWlkPWNrdWVobCxvdT1QZW9wbGUsZGM9T0NGLGRjPUJlcmtlbGV5LGRjPUVEVQ==
            changetype: add
            a:: Yg==
            a:: Yw==
        """).strip()

        mock_subprocess_check_output.assert_called_with(
            ('/usr/bin/ldapmodify', '-Q'),
            input=ldif,
            universal_newlines=True,
            timeout=10,
        )

        assert not mock_send_problem_report.called

    def test_normal_creation_keytab(self, mock_subprocess_check_output, mock_send_problem_report):
        create_ldap_entry(
            'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ['b', 'c'], 'd': 12, 'e': datetime(2016, 11, 5, 12, 0, 0, tzinfo=timezone(timedelta(hours=-7)))},
            keytab='/nonexist',
            admin_principal='create/admin',
        )

        # These are the base64-encoded versions of the attributes above
        ldif = dedent("""
            dn:: dWlkPWNrdWVobCxvdT1QZW9wbGUsZGM9T0NGLGRjPUJlcmtlbGV5LGRjPUVEVQ==
            changetype: add
            a:: Yg==
            a:: Yw==
            d:: MTI=
            e:: MjAxNjExMDUxMjAwMDAtMDcwMA==
        """).strip()

        mock_subprocess_check_output.assert_called_with(
            ('/usr/bin/kinit', '-t', '/nonexist', 'create/admin', '/usr/bin/ldapmodify', '-Q'),
            input=ldif,
            universal_newlines=True,
            timeout=10,
        )

        assert not mock_send_problem_report.called

    def test_create_existing(self, mock_subprocess_check_output, mock_send_problem_report):
        mock_subprocess_check_output.side_effect = CalledProcessError(68, 'cmd', output='Already exists (68)')
        with pytest.raises(ValueError) as error:
            create_ldap_entry(
                'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'a': ['b', 'c'], 'd': ['e']},
            )
        assert 'Tried to create duplicate entry.' in error.value.args
        assert not mock_send_problem_report.called

    def test_unexpected_error(self, mock_subprocess_check_output, mock_send_problem_report):
        mock_subprocess_check_output.side_effect = CalledProcessError(35, 'cmd', output='lol random error')
        with pytest.raises(ValueError) as error:
            create_ldap_entry(
                'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'a': ['b', 'c'], 'd': ['e']},
            )
        assert 'Unknown LDAP failure was encountered.' in error.value.args
        assert mock_send_problem_report.called

    def test_error_without_timezone(self, mock_subprocess_check_output):
        with pytest.raises(ValueError) as error:
            create_ldap_entry(
                'uid=ckuehl,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'datetime': datetime(2016, 11, 5, 12, 0, 0)},
            )
        assert 'Timestamp has no timezone info' in error.value.args
        assert mock_subprocess_check_output.assert_not_called


class TestModifyLdapEntry:

    def test_normal_modification(self, mock_subprocess_check_output, mock_send_problem_report):
        modify_ldap_entry(
            'uid=mattmcal,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ['b', 'c'], 'calnetUid': 1234},
        )

        # These are the base64-encoded versions of the attributes above
        ldif = dedent("""
            dn:: dWlkPW1hdHRtY2FsLG91PVBlb3BsZSxkYz1PQ0YsZGM9QmVya2VsZXksZGM9RURV
            changetype: modify
            replace: a
            a:: Yg==
            a:: Yw==
            -
            replace: calnetUid
            calnetUid:: MTIzNA==
            -
        """).strip()

        mock_subprocess_check_output.assert_called_with(
            ('/usr/bin/ldapmodify', '-Q'),
            input=ldif,
            universal_newlines=True,
            timeout=10,
        )

        assert not mock_send_problem_report.called

    def test_normal_modification_keytab(self, mock_subprocess_check_output, mock_send_problem_report):
        modify_ldap_entry(
            'uid=mattmcal,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'a': ['b', 'c'], 'calnetUid': 1234},
            keytab='/nonexist',
            admin_principal='create/admin'
        )

        # These are the base64-encoded versions of the attributes above
        ldif = dedent("""
            dn:: dWlkPW1hdHRtY2FsLG91PVBlb3BsZSxkYz1PQ0YsZGM9QmVya2VsZXksZGM9RURV
            changetype: modify
            replace: a
            a:: Yg==
            a:: Yw==
            -
            replace: calnetUid
            calnetUid:: MTIzNA==
            -
        """).strip()

        mock_subprocess_check_output.assert_called_with(
            ('/usr/bin/kinit', '-t', '/nonexist', 'create/admin', '/usr/bin/ldapmodify', '-Q'),
            input=ldif,
            universal_newlines=True,
            timeout=10,
        )

        assert not mock_send_problem_report.called

    def test_modify_nonexistent(self, mock_subprocess_check_output, mock_send_problem_report):
        mock_subprocess_check_output.side_effect = CalledProcessError(32, 'cmd', output='No such object (32)')
        with pytest.raises(ValueError) as error:
            modify_ldap_entry(
                'uid=unknown,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                {'a': ['b', 'c'], 'd': ['e']},
                keytab='/nonexist',
                admin_principal='create/admin'
            )
        assert 'Tried to modify nonexistent entry.' in error.value.args
        assert not mock_send_problem_report.called
