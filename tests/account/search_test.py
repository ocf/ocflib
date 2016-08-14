import pytest

from ocflib.account.search import user_attrs
from ocflib.account.search import user_attrs_ucb
from ocflib.account.search import user_exists
from ocflib.account.search import user_is_group
from ocflib.account.search import user_is_sorried
from ocflib.account.search import users_by_callink_oid
from ocflib.account.search import users_by_calnet_uid
from ocflib.account.search import users_by_filter


class TestUsersByFilter:

    @pytest.mark.parametrize('filter_str,results', [
        ('(uid=ckuehl)', {'ckuehl'}),
        ('(uidNumber=28460)', {'ckuehl'}),
        ('(|(uidNumber=28460)(uid=daradib))', {'ckuehl', 'daradib'}),
        ('(uid=doesnotexist)', set()),
        ('(herp=derp)', set()),
        ('(!(uid=*))', set()),
    ])
    def test_users_by_filter(self, filter_str, results):
        assert set(users_by_filter(filter_str)) == results

    @pytest.mark.parametrize('filter_str', ['', 'uid=ckuehl', '42', 'asdf'])
    def test_invalid_filters(self, filter_str):
        with pytest.raises(Exception):
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
        assert user['uidNumber'] == ['28460']

    def test_nonexistent_user(self):
        assert user_attrs('doesnotexist') is None


class TestUserAttrsUCB:

    def test_existing_user(self, test_uid=1034192):
        """These are a little flaky because alumni eventually get kicked out of
        the university's "People" OU. So you'll need to update these every few
        years."""
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
    ('sanjay', True),
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
