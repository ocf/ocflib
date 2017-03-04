import ocflib.account.search as search
import ocflib.infra.ldap as ldap
from ocflib.infra.ldap import UCB_LDAP_PEOPLE


def get_calnet_names(uid):
    """Returns CalNet LDAP entries relating to names"""

    attrs = search.user_attrs_ucb(uid)
    if attrs:
        return {key: attrs[key]
                for key in ('givenName', 'sn', 'displayName') if key in attrs}


def name_by_calnet_uid(uid):
    """Returns the name of CalNet person, searched by CalNet UID.

    Returns None on failure.
    """
    names = get_calnet_names(uid)

    if not names:
        return None

    # the name we want to input into our system is "givenName sn"
    # displayName is not necessarily equal to what's printed on Cal 1 Cards
    def get_longest_string(strs):
        return max(strs, key=len)

    if 'givenName' in names and 'sn' in names:
        given_name = get_longest_string(names['givenName'])
        sn = get_longest_string(names['sn'])

        if given_name and sn:
            return '{} {}'.format(given_name, sn)
    else:
        return names.get('displayName')


def calnet_uids_by_name(name):
    """Searches for people by name and returns any CalNet UIDs found.

    >>> calnet_uids_by_name("Dara Adib")
    [872544]
    """
    conds = ''.join(['(cn=*{}*)'.format(n) for n in name.split()])
    ldap_filter = '(&{})'.format(conds)

    with ldap.ldap_ucb() as c:
        c.search(UCB_LDAP_PEOPLE, ldap_filter, attributes=('uid',))
        return [int(entry['attributes']['uid'][0]) for entry in c.response]
