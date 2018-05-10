"""Information, stats, and control of printers."""
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1905 import NoSuchObject

PRINTERS = ['logjam', 'pagefault', 'papercut']

OID_TONER_MAX = '1.3.6.1.2.1.43.11.1.1.8.1.1'
OID_TONER_CUR = '1.3.6.1.2.1.43.11.1.1.9.1.1'

OID_MAINTKIT_MAX = '1.3.6.1.2.1.43.11.1.1.8.1.2'
OID_MAINTKIT_CUR = '1.3.6.1.2.1.43.11.1.1.9.1.2'

OID_LIFETIME_PAGES_PRINTED = '1.3.6.1.2.1.43.10.2.1.4.1.1'


def _snmp(host, oid):
    err_indication, err_status, err_idx, response_kv = (
        cmdgen.CommandGenerator().getCmd(
            cmdgen.CommunityData('my-agent', 'public', 0),
            cmdgen.UdpTransportTarget((host, 161)),
            oid,
        )
    )

    if err_indication:
        raise IOError(
            'Device {} returned error indication: {}'.format(host, err_indication),
        )
    elif err_status:
        raise IOError(
            'Device {} returned error status: {}'.format(host, err_status),
        )
    elif isinstance(response_kv[0][1], NoSuchObject):
        raise IOError(
            'Device {} returned error status: NoSuchObject()'.format(host),
        )
    else:
        return response_kv[0][1]


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
