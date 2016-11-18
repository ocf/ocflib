import mock
import pytest

from ocflib.ucb.directory import calnet_uids_by_name
from ocflib.ucb.directory import name_by_calnet_uid
from tests.conftest import TEST_PERSON_CALNET_UID
from tests.conftest import TEST_PERSON_NAME


class TestNameByCalNetUID:

    @pytest.mark.parametrize('attrs,expected', [
        ({'givenName': ['Jason'], 'sn': ['Perrin']}, 'Jason Perrin'),
        ({'displayName': 'Matthew McAllister'}, 'Matthew McAllister'),
        ({}, None),
    ])
    def test_name_by_calnet_uid(self, attrs, expected):
        """This tests that the 'displayName' fallback works without hitting
        UCB LDAP, since we can't actually control entries there."""
        with mock.patch(
            'ocflib.account.search.user_attrs_ucb',
            return_value=attrs
        ):
            assert name_by_calnet_uid(0) == expected

    @pytest.mark.parametrize('uid,expected', [
        (TEST_PERSON_CALNET_UID, TEST_PERSON_NAME),
        (9999999, None),
    ])
    def test_name_by_calnet_uid_real_query(self, uid, expected):
        assert name_by_calnet_uid(uid) == expected


class TestCalNetUIDsByName:

    @pytest.mark.parametrize('name,expected', [
        (TEST_PERSON_NAME, [TEST_PERSON_CALNET_UID]),
        ('~~~', []),
    ])
    def test_calnet_uids_by_name(self, name, expected):
        assert calnet_uids_by_name(name) == expected
