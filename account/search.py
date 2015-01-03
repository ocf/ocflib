"""Methods for searching and selecting users."""
import alib.constants
# TODO: imports

def users_by_calnet_uid(calnet_uid):
    """Get a list of users associated with a CalNet UID"""

    l = ldap.initialize(alib.constants.OCF_LDAP)
    l.simple_bind_s("", "")

    search_filter = "(calnetUid=%s)" % calnet_uid
    attrs = ["uid"]

    ldap_entries = l.search_st(alib.constants.OCF_LDAP_BASE,
                               ldap.SCOPE_SUBTREE, search_filter, attrs)

    return [entry[1]["uid"][0] for entry in ldap_entries]

def user_attrs(user_account):
    """Returns a dictionary of LDAP attributes for a given LDAP UID in
    the form:

    {
      'uid': ['somebody'],
      'objectClass': ['ocfAccount', 'account', 'posixAccount'],
      'loginShell': ['/bin/zsh']
    }

    Returns None if no account exists with uid=user_account.
    """

    l = ldap.initialize(alib.constants.OCF_LDAP)
    l.simple_bind_s("", "")

    search_filter = "(uid=%s)" % user_account

    ldap_entries = l.search_st(alib.constants.OCF_LDAP_BASE,
                               ldap.SCOPE_SUBTREE, search_filter)

    if len(ldap_entries) > 0:
        return ldap_entries[0][1]

def user_exists(user_account):
    """Returns True if an OCF user exists with specified account name"""

    l = ldap.initialize(alib.constants.OCF_LDAP)
    l.simple_bind_s("", "")

    search_filter = "(uid=%s)" % user_account
    attrs = []
    ldap_entries = l.search_st(alib.constants.OCF_LDAP_BASE,
                               ldap.SCOPE_SUBTREE, search_filter, attrs)

    return len(ldap_entries) == 1
