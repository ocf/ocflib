try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.parse import urljoin

import ocflib.account.search as search
import ocflib.constants as constants


def verify_ticket(ticket, service):
    """Verifies CAS 2.0+ XML-based authentication ticket.

    Returns CalNet UID on success and None on failure.
    """
    params = {'ticket': ticket, 'service': service}
    url = (urljoin(constants.CAS_URL, 'serviceValidate') + '?' +
           urlencode(params))
    try:
        page = urlopen(url)
        response = page.read()
        tree = ElementTree.fromstring(response)
        if tree[0].tag.endswith('authenticationSuccess'):
            return tree[0][0].text
        else:
            return None
    except:
        return None


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
    get_longest_string = lambda strs: max(strs, key=len)

    if 'givenName' in names and 'sn' in names:
        given_name = get_longest_string(names['givenName'])
        sn = get_longest_string(names['sn'])

        if given_name and sn:
            return "{} {}".format(given_name, sn)
    elif 'displayName' in names:
        display_name = get_longest_string(names["displayName"])

        if display_name:
            return display_name
