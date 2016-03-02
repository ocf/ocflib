"""DEPRECATED.

This module has been moved to ocflib.printing.printers. In a future version,
this module will be removed entirely.
"""
from ocflib.printing.printers import _snmp  # noqa
from ocflib.printing.printers import get_lifetime_pages  # noqa
from ocflib.printing.printers import get_maintkit  # noqa
from ocflib.printing.printers import get_toner  # noqa
from ocflib.printing.printers import OID_LIFETIME_PAGES_PRINTED  # noqa
from ocflib.printing.printers import OID_MAINTKIT_CUR  # noqa
from ocflib.printing.printers import OID_MAINTKIT_MAX  # noqa
from ocflib.printing.printers import OID_TONER_CUR  # noqa
from ocflib.printing.printers import OID_TONER_MAX  # noqa
from ocflib.printing.printers import PRINTERS  # noqa

# TODO: fix callers of this module
