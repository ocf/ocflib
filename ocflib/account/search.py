"""Methods for searching and selecting users."""
import ldap3

import ocflib.constants as constants
import ocflib.account.ldap as ldap


def users_by_calnet_uid(calnet_uid):
    """Get a list of users associated with a CalNet UID"""
    with ldap.ldap_ocf() as c:
        c.search(constants.OCF_LDAP_PEOPLE,
                 "(calnetUid={})".format(calnet_uid), attributes=('uid',))
        return [entry['attributes']['uid'][0] for entry in c.response]


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
        c.search(base, "(uid={})".format(uid), attributes=ldap3.ALL_ATTRIBUTES)

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
    return 'callinkOid' in attrs or 'oslGid' in attrs
