"""Methods for searching and selecting users."""
import ldap3

import ocflib.infra.ldap as ldap
from ocflib.infra.ldap import OCF_LDAP_PEOPLE
from ocflib.infra.ldap import UCB_LDAP_PEOPLE

SORRIED_SHELL = '/opt/share/utils/bin/sorried'


def users_by_filter(ldap_filter):
    """Returns a list of users matching an LDAP filter"""
    with ldap.ldap_ocf() as c:
        c.search(
            OCF_LDAP_PEOPLE,
            ldap_filter,
            attributes=('uid',),
            search_scope=ldap3.LEVEL,
        )
        return [entry['attributes']['uid'][0] for entry in c.response]


def users_by_calnet_uid(calnet_uid):
    """Get a list of users associated with a CalNet UID"""
    calnet_uid = int(calnet_uid)
    return users_by_filter('(calnetUid={})'.format(calnet_uid))


def users_by_callink_oid(callink_oid):
    """Get a list of users associated with a CalLink OID"""
    callink_oid = int(callink_oid)
    return users_by_filter('(callinkOid={})'.format(callink_oid))


def user_attrs(uid, connection=ldap.ldap_ocf, base=OCF_LDAP_PEOPLE):
    """Returns a dictionary of LDAP attributes for a given LDAP UID.

    The returned dictionary looks like:
    {
      'uid': ['somebody'],
      'objectClass': ['ocfAccount', 'account', 'posixAccount'],
      'loginShell': ['/bin/zsh']
    }

    Returns None if no account exists with uid=user_account.
    """
    with connection() as c:
        c.search(base, '(uid={})'.format(uid), attributes=ldap3.ALL_ATTRIBUTES)

        if len(c.response) > 0:
            return c.response[0]['attributes']


def user_attrs_ucb(uid):
    return user_attrs(uid, connection=ldap.ldap_ucb,
                      base=UCB_LDAP_PEOPLE)


def user_exists(account):
    """Returns whether username is an OCF account."""
    return bool(user_attrs(account))


def user_is_sorried(account):
    shell = user_attrs(account)['loginShell']
    return shell == SORRIED_SHELL


def user_is_group(username):
    """Returns whether username is an OCF group account."""
    attrs = user_attrs(username)
    return 'callinkOid' in attrs
