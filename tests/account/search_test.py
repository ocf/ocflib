import pytest

from ocflib.account.search import users_by_filter
from ocflib.account.search import users_by_calnet_uid
from ocflib.account.search import users_by_callink_oid
from ocflib.account.search import user_exists
from ocflib.account.search import user_is_group
from ocflib.account.search import user_attrs
from ocflib.account.search import user_attrs_ucb


def test_users_by_filter():
    assert users_by_filter('(uid=ckuehl)') == ['ckuehl']
    assert users_by_filter('(uidNumber=28460)') == ['ckuehl']
    assert set(users_by_filter('(|(uidNumber=28460)(uid=daradib))')) == {'ckuehl', 'daradib'}

    assert users_by_filter('(uid=doesnotexist)') == []
    assert users_by_filter('(herp=derp)') == []

    # invalid filters
    for bad_filter in ['', 'uid=ckuehl', '42', 'asdf hjkl']:
        with pytest.raises(Exception):
            users_by_filter(bad_filter)


def test_users_by_calnet_uid():
    assert users_by_calnet_uid(872544) == ['daradib']
    assert users_by_calnet_uid(666666) == []


def test_users_by_callink_oid():
    assert users_by_callink_oid(46130) == ['bpreview']
    assert users_by_callink_oid(666666) == []


def test_user_attrs():
    user = user_attrs('ckuehl')
    assert user['uid'] == ['ckuehl']
    assert user['uidNumber'] == ['28460']

    # non-existant user
    assert user_attrs('doesnotexist') is None


def test_user_attrs_ucb(test_uid=1034192):
    """These are a little flaky because alumni eventually get kicked out of the
    university's "People" OU. So you'll need to update these every few
    years."""
    user = user_attrs_ucb(test_uid)
    assert user['uid'] == [str(test_uid)]
    assert 'person' in user['objectClass']


def test_user_exists():
    assert user_exists('ckuehl')
    assert user_exists('bpreview')
    assert not user_exists('doesnotexist')


def test_user_is_group():
    assert user_is_group('bpreview')
    assert user_is_group('decal')
    assert not user_is_group('daradib')

    with pytest.raises(Exception):
        user_is_group('doesnotexist')
