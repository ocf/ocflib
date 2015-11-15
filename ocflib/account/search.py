"""Methods for searching and selecting users."""
import ldap3

import ocflib.constants as constants
import ocflib.infra.ldap as ldap


def users_by_filter(ldap_filter):
    """Returns a list of users matching an LDAP filter"""
    return []


def users_by_calnet_uid(calnet_uid):
    """Get a list of users associated with a CalNet UID"""
    calnet_uid = int(calnet_uid)
    return users_by_filter('(calnetUid={})'.format(calnet_uid))


def users_by_callink_oid(callink_oid):
    """Get a list of users associated with a CalLink OID"""
    callink_oid = int(callink_oid)
    return users_by_filter('(callinkOid={})'.format(callink_oid))


def user_attrs(uid, connection=ldap.ldap_ocf, base=constants.OCF_LDAP_PEOPLE):
    """Returns a dictionary of LDAP attributes for a given LDAP UID in
    the form:

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
                      base=constants.UCB_LDAP_PEOPLE)


def user_exists(account):
    """Returns True if an OCF user exists with specified account name"""
    return bool(user_attrs(account))


def user_is_group(username):
    """Returns True if an OCF user account exists and is a group account"""
    attrs = user_attrs(username)
    return 'callinkOid' in attrs
