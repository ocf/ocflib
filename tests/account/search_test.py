import pytest
from ldap3.core.exceptions import LDAPAttributeError

from ocflib.account.search import user_attrs
from ocflib.account.search import user_attrs_ucb
from ocflib.account.search import user_exists
from ocflib.account.search import user_is_group
from ocflib.account.search import user_is_sorried
from ocflib.account.search import users_by_callink_oid
from ocflib.account.search import users_by_calnet_uid
from ocflib.account.search import users_by_filter
from ocflib.account.search import users_in_group
from tests.conftest import TEST_PERSON_CALNET_UID


class TestUsersByFilter:

    @pytest.mark.parametrize('filter_str,results', [
        ('(uid=ckuehl)', {'ckuehl'}),
        ('(uidNumber=28460)', {'ckuehl'}),
        ('(|(uidNumber=28460)(uid=daradib))', {'ckuehl', 'daradib'}),
        ('(uid=doesnotexist)', set()),
        ('(!(uid=*))', set()),
    ])
    def test_users_by_filter(self, filter_str, results):
        assert set(users_by_filter(filter_str)) == results

    @pytest.mark.parametrize('filter_str', ['', 'uid=ckuehl', '42', 'asdf'])
    def test_invalid_filters(self, filter_str):
        with pytest.raises(Exception):
            users_by_filter(filter_str)

    def test_invalid_ldap_attr(self, filter_str='(herp=derp)'):
        with pytest.raises(LDAPAttributeError):
            users_by_filter(filter_str)


@pytest.mark.parametrize('uid,users', [
    (872544, ['daradib']),
    (666666, []),
])
def test_users_by_calnet_uid(uid, users):
    assert users_by_calnet_uid(uid) == users


@pytest.mark.parametrize('oid,users', [
    (46130, ['bpreview']),
    (666666, []),
])
def test_users_by_callink_oid(oid, users):
    assert users_by_callink_oid(oid) == users


class TestUserAttrs:

    def test_existing_user(self):
        user = user_attrs('ckuehl')
        assert user['uid'] == ['ckuehl']
        assert user['uidNumber'] == 28460

    def test_nonexistent_user(self):
        assert user_attrs('doesnotexist') is None


class TestUserAttrsUCB:

    def test_existing_user(self, test_uid=TEST_PERSON_CALNET_UID):
        user = user_attrs_ucb(test_uid)
        assert user['uid'] == [str(test_uid)]
        assert 'person' in user['objectClass']

    def test_nonexistent_user(self):
        assert user_attrs_ucb(9999999999) is None


@pytest.mark.parametrize('user,exists', [
    ('ckuehl', True),
    ('bpreview', True),
    ('doesnotexist', False),
])
def test_user_exists(user, exists):
    assert user_exists(user) == exists


@pytest.mark.parametrize('user,sorried', [
    ('ckuehl', False),
    ('ofc', True),
])
def test_user_is_sorried(user, sorried):
    assert user_is_sorried(user) == sorried


class TestUserIsGroup:

    @pytest.mark.parametrize('user,exists', [
        ('ckuehl', False),
        ('bpreview', True),
    ])
    def test_user_is_group(self, user, exists):
        assert user_is_group(user) == exists

    def test_notexistent_user(self):
        with pytest.raises(Exception):
            user_is_group('doesnotexist')


@pytest.mark.parametrize('user,group,is_in', [
    ('ckuehl', 'ocfroot', True),
    ('gstaff', 'ocfstaff', True),
    ('guser', 'ocfstaff', False),
    ('testopstaff', 'opstaff', True),
])
def test_user_is_in_group(user, group, is_in):
    assert (user in users_in_group(group)) == is_in
