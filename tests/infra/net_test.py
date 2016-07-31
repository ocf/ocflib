from ipaddress import ip_address

import pytest

from ocflib.infra.net import ipv4_to_ipv6
from ocflib.infra.net import ipv6_to_ipv4
from ocflib.infra.net import is_ocf_ip
from ocflib.infra.net import OCF_DNS_RESOLVER
from ocflib.infra.net import OCF_GATEWAY_V4
from ocflib.infra.net import OCF_GATEWAY_V6
from ocflib.infra.net import OCF_SUBNET_V4
from ocflib.infra.net import OCF_SUBNET_V6


TEST_IPV4_IPV6 = (
    ('169.229.226.23', '2607:f140:8801::1:23'),
    ('169.229.226.10', '2607:f140:8801::1:10'),
    ('169.229.226.208', '2607:f140:8801::1:208'),
)


def test_constants_are_sane():
    assert OCF_DNS_RESOLVER in OCF_SUBNET_V4
    assert OCF_GATEWAY_V4 in OCF_SUBNET_V4
    assert OCF_GATEWAY_V6 in OCF_SUBNET_V6


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


@pytest.mark.parametrize('ip,expected', [
    (ip_address('169.229.226.12'), True),
    (ip_address('169.229.226.1'), True),
    (ip_address('169.229.226.212'), True),
    (ip_address('2607:f140:8801::10'), True),
    (ip_address('2607:f140:8801::1:10'), True),

    (ip_address('8.8.8.8'), False),
    (ip_address('cafe:f140:8801::1:10'), False),
])
def test_is_ocf_ip(ip, expected):
    assert is_ocf_ip(ip) is expected


def test_is_ocf_ip_failure():
    with pytest.raises(AssertionError):
        is_ocf_ip('169.229.226.12')
