from ipaddress import ip_address

import pytest

from ocflib.infra.net import ipv4_to_ipv6
from ocflib.infra.net import ipv6_to_ipv4


TEST_IPV4_IPV6 = (
    ('169.229.226.23', '2607:f140:8801::1:23'),
    ('169.229.226.10', '2607:f140:8801::1:10'),
    ('169.229.226.208', '2607:f140:8801::1:208'),
)


@pytest.mark.parametrize('ipv4,ipv6', TEST_IPV4_IPV6)
def test_4to6(ipv4, ipv6):
    assert ipv4_to_ipv6(ip_address(ipv4)) == ip_address(ipv6)


@pytest.mark.parametrize('ipv4', [
    # string not ok
    '169.229.226.12',
    # wrong subnet
    ip_address('169.229.10.12'),
    # wrong version
    ip_address('2607:f140:8801::1:10'),
])
def test_4to6_failure(ipv4):
    with pytest.raises(AssertionError):
        ipv4_to_ipv6(ipv4)


@pytest.mark.parametrize('ipv4,ipv6', TEST_IPV4_IPV6)
def test_6to4(ipv4, ipv6):
    assert ipv6_to_ipv4(ip_address(ipv6)) == ip_address(ipv4)


@pytest.mark.parametrize('ipv6', [
    # string not ok
    '2607:f140:8801::1:10',
    # wrong version
    ip_address('169.229.10.12'),
    # wrong subnet entirely
    ip_address('cafe:f140:8801::1:10'),
    # not in compat subnet
    ip_address('2607:f140:8801::10'),
])
def test_6to4_failure(ipv6):
    with pytest.raises(AssertionError):
        ipv6_to_ipv4(ipv6)
