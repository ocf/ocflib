from urllib.parse import urlencode
from urllib.parse import urljoin
from xml.etree import ElementTree

import requests

CAS_URL = 'https://auth.berkeley.edu/cas/'


def verify_ticket(ticket, service):
    """Verifies CAS 2.0+ XML-based authentication ticket.

    Returns CalNet UID on success and None on failure.
    """
    params = {'ticket': ticket, 'service': service}
    url = (urljoin(CAS_URL, 'serviceValidate') + '?' +
           urlencode(params))
    try:
        req = requests.get(url)
        tree = ElementTree.fromstring(req.text)
        if tree[0].tag.endswith('authenticationSuccess'):
            return tree[0][0].text
        else:
            return None
    except Exception:
        return None
