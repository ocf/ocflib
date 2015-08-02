import ocflib.account.search as search


def get_calnet_names(uid):
    """Returns CalNet LDAP entries relating to names"""

    attrs = search.user_attrs_ucb(uid)
    if attrs:
        return {key: attrs[key]
                for key in ('givenName', 'sn', 'displayname') if attrs[key]}


def name_by_calnet_uid(uid):
    """Returns the name of CalNet person, searched by CalNet UID.

    Returns None on faliure.
    """
    names = get_calnet_names(uid)

    # the name we want to input into our system is "givenName sn"
    # displayName is not necessarily equal to what's printed on Cal 1 Cards
    def get_longest_string(strs):
        return max(strs, key=len)

    if 'givenName' in names and 'sn' in names:
        given_name = get_longest_string(names['givenName'])
        sn = get_longest_string(names['sn'])

        if given_name and sn:
            return '{} {}'.format(given_name, sn)
    elif 'displayName' in names:
        display_name = get_longest_string(names['displayName'])

        if display_name:
            return display_name
