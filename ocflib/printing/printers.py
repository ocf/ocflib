"""Information, stats, and control of printers."""
import asyncio

import puresnmp

PRINTERS = ['logjam', 'pagefault', 'papercut', 'fishpaper']

OID_TONER_MAX = '1.3.6.1.2.1.43.11.1.1.8.1.1'
OID_TONER_CUR = '1.3.6.1.2.1.43.11.1.1.9.1.1'

OID_MAINTKIT_MAX = '1.3.6.1.2.1.43.11.1.1.8.1.2'
OID_MAINTKIT_CUR = '1.3.6.1.2.1.43.11.1.1.9.1.2'

OID_LIFETIME_PAGES_PRINTED = '1.3.6.1.2.1.43.10.2.1.4.1.1'


def _snmp(host, oid):
    try:
        client = puresnmp.PyWrapper(puresnmp.Client(host, puresnmp.V2C('public')))
        return asyncio.run(client.get(oid))
    except Exception as e:
        raise IOError('Device {} returned SNMP error: {}'.format(host, e)) from e


def get_toner(printer):
    """Returns (cur, max) toner tuple for the given printer."""
    return tuple(
        int(_snmp(printer, oid))
        for oid in (OID_TONER_CUR, OID_TONER_MAX)
    )


def get_maintkit(printer):
    """Returns (cur, max) maintenance kit tuple for the given printer."""
    return tuple(
        int(_snmp(printer, oid))
        for oid in (OID_MAINTKIT_CUR, OID_MAINTKIT_MAX)
    )


def get_lifetime_pages(printer):
    """Returns lifetime pages printed for the given printer."""
    return int(_snmp(printer, OID_LIFETIME_PAGES_PRINTED))
