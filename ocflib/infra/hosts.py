"""Methods for working with OCF hosts."""
import ldap3

import ocflib.constants as constants
import ocflib.infra.ldap as ldap


def hosts_by_filter(ldap_filter):
    """Return a list of hosts satisfying the LDAP filter."""

    with ldap.ldap_ocf() as c:
        c.search(
            constants.OCF_LDAP_HOSTS,
            ldap_filter,
            attributes=ldap3.ALL_ATTRIBUTES,
        )

        return [entry['attributes'] for entry in c.response]
