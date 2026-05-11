"""Information, stats, and control of printers."""
import asyncio

import puresnmp

PRINTERS = ['logjam', 'pagefault', 'papercut', 'fishpaper']

OID_TONER_MAX = '1.3.6.1.2.1.43.11.1.1.8.1.1'
OID_TONER_CUR = '1.3.6.1.2.1.43.11.1.1.9.1.1'

OID_MAINTKIT_MAX = '1.3.6.1.2.1.43.11.1.1.8.1.2'
OID_MAINTKIT_CUR = '1.3.6.1.2.1.43.11.1.1.9.1.2'

OID_LIFETIME_PAGES_PRINTED = '1.3.6.1.2.1.43.10.2.1.4.1.1'

OID_STATUS = '1.3.6.1.2.1.43.16.5.1.2.1'

OID_TRAY_MAX = '1.3.6.1.2.1.43.8.2.1.9.1'
OID_TRAY_CUR = '1.3.6.1.2.1.43.8.2.1.10.1'
OID_TRAY_NAME = '1.3.6.1.2.1.43.8.2.1.13.1'


def _snmp(host, oid):
    try:
        client = puresnmp.PyWrapper(puresnmp.Client(host, puresnmp.V2C('public')))
        return asyncio.run(client.get(oid))
    except Exception as e:
        raise IOError('Device {} returned SNMP error: {}'.format(host, e)) from e


def _snmp_walk(host, oid):
    try:
        client = puresnmp.PyWrapper(puresnmp.Client(host, puresnmp.V2C('public')))

        async def _collect():
            return [item async for item in client.walk(oid)]

        return asyncio.run(_collect())
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


def get_paper_trays(printer):
    """Returns a list of (name, cur, max) tuples for each input tray.

    cur and max are sheet counts. Tray 1 (manual/multipurpose feed) and trays
    where the current level is not sensed by the printer (negative value) are
    excluded.
    """
    def _decode(v):
        return v.decode() if isinstance(v, bytes) else str(v)

    names_raw = _snmp_walk(printer, OID_TRAY_NAME)
    maxes_raw = _snmp_walk(printer, OID_TRAY_MAX)
    curs_raw = _snmp_walk(printer, OID_TRAY_CUR)

    trays = []
    for (_, name), (_, max_val), (_, cur_val) in zip(names_raw, maxes_raw, curs_raw):
        name = _decode(name)
        max_val = int(max_val)
        cur_val = int(cur_val)
        if name == 'Tray 1' or max_val <= 0 or cur_val < 0:
            continue
        trays.append((name, cur_val, max_val))
    return trays


def get_status(printer):
    """Returns a list of non-empty status strings for the given printer.

    Status messages are read from the printer's display/alert table
    (SNMPv2-SMI::mib-2.43.16.5.1.2.1). Empty entries are omitted.
    """
    results = _snmp_walk(printer, OID_STATUS)
    return [value.decode() if isinstance(value, bytes) else str(value) for _, value in results if value]
