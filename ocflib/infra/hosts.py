"""Methods for working with OCF hosts."""
import ldap3
from ldap3.utils.conv import escape_filter_chars

import ocflib.infra.ldap as ldap
from ocflib.infra.ldap import OCF_LDAP_HOSTS

HOST_TYPES_WITH_IPV6 = frozenset({
    'desktop',
    'dhcp',
    'server',
    'staffvm',
    'switch',
    'vip',
    'wifi',
})


def hosts_by_filter(ldap_filter):
    """Return a list of hosts satisfying the LDAP filter.

    The list returned contains a dictionary of LDAP attributes for each host.
    """

    with ldap.ldap_ocf() as c:
        c.search(
            OCF_LDAP_HOSTS,
            ldap_filter,
            attributes=ldap3.ALL_ATTRIBUTES,
        )

        return [entry['attributes'] for entry in c.response]


def hostname_from_domain(fqdn):
    """Extracts the hostname from its canonical domain.

    >>> hostname_from_domain('death.ocf.berkeley.edu')
    'death'
    """
    return fqdn.split('.')[0]


def domain_from_hostname(hostname):
    """Return the canonical domain from a hostname, and if it's already a hostname, just return itself.

    >>> domain_from_hostname('tsunami')
    'tsunami.ocf.berkeley.edu'
    """
    if not hostname.endswith('.ocf.berkeley.edu'):
        return hostname + '.ocf.berkeley.edu'
    return hostname


def type_of_host(hostname):
    """Returns the type of a host as specified in LDAP.

    >>> type_of_host('eruption')
    'desktop'
    >>> type_of_host('supernova')
    'server'
    """
    hosts = hosts_by_filter('(cn={})'.format(escape_filter_chars(hostname)))
    return hosts[0]['type'] if hosts else None
