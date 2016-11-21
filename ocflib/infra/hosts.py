"""Methods for working with OCF hosts."""
import ldap3

import ocflib.constants as constants
import ocflib.infra.ldap as ldap


HOST_TYPES_WITH_IPV6 = frozenset({
    'desktop',
    'dhcp',
    'server',
    'staffvm',
    'switch',
    'wifi',
})


def hosts_by_filter(ldap_filter):
    """Return a list of hosts satisfying the LDAP filter.

    The list returned contains a dictionary of LDAP attributes for each host.
    """

    with ldap.ldap_ocf() as c:
        c.search(
            constants.OCF_LDAP_HOSTS,
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


def type_of_host(hostname):
    """Returns the type of a host as specified in LDAP.

    >>> type_of_host('eruption')
    'desktop'
    >>> type_of_host('supernova')
    'server'
    """
    hosts = hosts_by_filter('(cn={})'.format(hostname))
    return hosts[0]['type'] if hosts else None
