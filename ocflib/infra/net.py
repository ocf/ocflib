"""Networking."""
from ipaddress import ip_address
from ipaddress import ip_network
from ipaddress import IPv4Address
from ipaddress import IPv6Address

OCF_SUBNET_V4 = ip_network('169.229.226.0/24')
OCF_SUBNET_V6 = ip_network('2607:f140:8801::/64')
OCF_SUBNET_V6_COMPAT = ip_network('2607:f140:8801::1:0/112')
OCF_DNS_RESOLVER = ip_address('169.229.226.22')


def ipv6_to_ipv4(ipv6):
    """Convert an OCF IPv6 address to its equivalent IPv4.

    This works only for IPs in our "compatibility" subnet, which is a special
    subnet where we map one-to-one hosts from IPv4 to IPv6.

    Note that the bits do *not* map exactly, since IPv6 is written in
    hexadecimal, whereas IPv4 is written in decimal. For the benefit of humans,
    we make the human-readable portion the same, not the binary representation.
    """
    assert isinstance(ipv6, IPv6Address)
    assert ipv6 in OCF_SUBNET_V6_COMPAT
    last_group = int(ipv6.exploded.split(':')[-1])
    return ip_address(
        int.from_bytes(OCF_SUBNET_V4.network_address.packed, 'big') | last_group
    )


def ipv4_to_ipv6(ipv4):
    """Convert an OCF IPv4 address to its equivalent compatibility IPv4.

    For a description of the compability IPv6 subnet, see `ipv6_to_ipv4` above.
    """
    assert isinstance(ipv4, IPv4Address)
    assert ipv4 in OCF_SUBNET_V4
    last_group = int(ipv4.exploded.split('.')[-1], 16)
    return ip_address(
        int.from_bytes(OCF_SUBNET_V6_COMPAT.network_address.packed, 'big') | last_group
    )


def is_ocf_ip(ip):
    """Return whether this IP is owned by the OCF.

    Accepts both IPv4 and IPv6 addresses in object form from the ipaddress
    module.

    >>> from ipaddress import ip_address
    >>> is_ocf_ip(ip_address('169.229.226.12'))
    True
    """
    if isinstance(ip, IPv4Address):
        return ip in OCF_SUBNET_V4
    elif isinstance(ip, IPv6Address):
        return ip in OCF_SUBNET_V6
    else:
        raise AssertionError('You must pass in an IPv4Address or IPv6Address object.')
