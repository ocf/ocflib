from unittest import mock
import pytest

from ocflib.account.officers import add_officer_role
from ocflib.account.officers import all_officer_roles
from ocflib.account.officers import decode
from ocflib.account.officers import encode
from ocflib.account.officers import is_officer
from ocflib.account.officers import OFFICER_OBJECT_CLASSES
from ocflib.account.officers import officer_roles
from ocflib.account.officers import OfficerRole
from ocflib.account.officers import remove_officer_role


def _role(role, term, committee=None):
    return OfficerRole(
        uid='someuser', name='Some User', role=role, term=term,
        committee=committee,
    )


class TestEncodeDecodeRole:

    def test_encode_without_committee(self):
        assert encode('gm', 'Fall 2026') == 'role=gm;term=Fall 2026'

    def test_encode_with_committee(self):
        assert encode('head', 'Fall 2026', committee='Internal') == \
            'role=head;committee=Internal;term=Fall 2026'

    def test_decode_without_committee(self):
        role = decode('someuser', 'Some User', 'role=gm;term=Fall 2026')
        assert role == OfficerRole(
            uid='someuser', name='Some User', role='gm',
            term='Fall 2026', committee=None,
        )

    def test_decode_with_committee(self):
        role = decode(
            'someuser', 'Some User',
            'role=head;committee=Internal;term=Fall 2026',
        )
        assert role == OfficerRole(
            uid='someuser', name='Some User', role='head',
            term='Fall 2026', committee='Internal',
        )

    def test_encode_decode_round_trip(self):
        encoded = encode('head', 'Spring 2025', committee='DeCal')
        decoded = decode('someuser', 'Some User', encoded)
        assert decoded.role == 'head'
        assert decoded.term == 'Spring 2025'
        assert decoded.committee == 'DeCal'


class TestOfficerRoles:

    def test_user_with_single_role(self):
        roles = officer_roles('ahilan')
        assert roles == [
            OfficerRole(
                uid='ahilan', name='Ahilan Anantha', role='sm',
                term='Spring 1998', committee=None,
            ),
        ]

    def test_user_with_multiple_roles(self):
        roles = officer_roles('ckuehl')
        assert len(roles) > 1
        assert all(r.role == 'sm' for r in roles)
        assert all(r.uid == 'ckuehl' for r in roles)

    def test_user_with_committee_roles(self):
        roles = officer_roles('adi')
        committees = {r.committee for r in roles if r.role == 'head'}
        assert 'Finance' in committees

    def test_user_never_an_officer(self):
        assert officer_roles('bpreview') == []

    def test_nonexistent_user(self):
        assert officer_roles('doesnotexist') == []


class TestAllOfficerRoles:

    def test_returns_known_officers(self):
        roles = all_officer_roles()
        uids = {r.uid for r in roles}
        assert 'ahilan' in uids
        assert 'ckuehl' in uids

    def test_only_returns_officers(self):
        roles = all_officer_roles()
        uids = {r.uid for r in roles}
        assert 'bpreview' not in uids


class TestIsOfficer:

    @pytest.mark.parametrize('uid,expected', [
        ('ahilan', True),
        ('ckuehl', True),
        ('bpreview', False),
        ('doesnotexist', False),
    ])
    def test_is_officer(self, uid, expected):
        assert is_officer(uid) == expected


class TestAddOfficerRole:

    def test_add_first_role(self):
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=[],
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            add_officer_role('someuser', 'gm', 'Fall 2026')

        modify.assert_called_once_with(
            'uid=someuser,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {
                'objectClass': OFFICER_OBJECT_CLASSES,
                'ocfOfficerRole': ['role=gm;term=Fall 2026'],
            },
        )

    def test_add_preserves_existing_roles(self):
        existing = [_role('sm', 'Spring 2025')]
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=existing,
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            add_officer_role('someuser', 'gm', 'Fall 2025')

        assert modify.call_args[0][1]['ocfOfficerRole'] == [
            'role=sm;term=Spring 2025',
            'role=gm;term=Fall 2025',
        ]

    def test_add_head_role_with_committee(self):
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=[],
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            add_officer_role(
                'someuser', 'head', 'Fall 2026', committee='Internal',
            )

        assert modify.call_args[0][1]['ocfOfficerRole'] == [
            'role=head;committee=Internal;term=Fall 2026',
        ]

    def test_add_head_role_without_committee_raises(self):
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=[],
            ),
            mock.patch('ocflib.account.officers.modify_ldap_entry'),
        ):
            with pytest.raises(ValueError):
                add_officer_role('someuser', 'head', 'Fall 2026')

    def test_add_invalid_role_raises(self):
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=[],
            ),
            mock.patch('ocflib.account.officers.modify_ldap_entry'),
        ):
            with pytest.raises(ValueError):
                add_officer_role('someuser', 'president', 'Fall 2026')

    def test_add_duplicate_role_raises(self):
        existing = [_role('gm', 'Fall 2026')]
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=existing,
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            with pytest.raises(ValueError):
                add_officer_role('someuser', 'gm', 'Fall 2026')

        modify.assert_not_called()

    def test_add_passes_through_kwargs(self):
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=[],
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            add_officer_role(
                'someuser', 'gm', 'Fall 2026',
                keytab='/some.keytab', admin_principal='admin',
            )

        assert modify.call_args[1] == {
            'keytab': '/some.keytab',
            'admin_principal': 'admin',
        }


class TestRemoveOfficerRole:

    def test_remove_only_role(self):
        existing = [_role('gm', 'Fall 2026')]
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=existing,
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            remove_officer_role('someuser', 'gm', 'Fall 2026')

        modify.assert_called_once_with(
            'uid=someuser,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
            {'ocfOfficerRole': []},
        )

    def test_remove_one_of_several_roles(self):
        existing = [
            _role('gm', 'Fall 2025'), _role('gm', 'Spring 2026'),
        ]
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=existing,
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            remove_officer_role('someuser', 'gm', 'Fall 2025')

        assert modify.call_args[0][1]['ocfOfficerRole'] == [
            'role=gm;term=Spring 2026',
        ]

    def test_remove_head_role_matches_on_committee(self):
        existing = [
            _role('head', 'Fall 2025', committee='Internal'),
            _role('head', 'Fall 2025', committee='Finance'),
        ]
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=existing,
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            remove_officer_role(
                'someuser', 'head', 'Fall 2025', committee='Internal',
            )

        assert modify.call_args[0][1]['ocfOfficerRole'] == [
            'role=head;committee=Finance;term=Fall 2025',
        ]

    def test_remove_nonexistent_role_raises(self):
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=[],
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            with pytest.raises(ValueError):
                remove_officer_role('someuser', 'gm', 'Fall 2026')

        modify.assert_not_called()

    def test_remove_passes_through_kwargs(self):
        existing = [_role('gm', 'Fall 2026')]
        with (
            mock.patch(
                'ocflib.account.officers.officer_roles',
                return_value=existing,
            ),
            mock.patch(
                'ocflib.account.officers.modify_ldap_entry',
            ) as modify,
        ):
            remove_officer_role(
                'someuser', 'gm', 'Fall 2026',
                keytab='/some.keytab', admin_principal='admin',
            )

        assert modify.call_args[1] == {
            'keytab': '/some.keytab',
            'admin_principal': 'admin',
        }
