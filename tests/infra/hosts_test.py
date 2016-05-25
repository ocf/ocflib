import pytest

from ocflib.infra.hosts import hostname_from_domain
from ocflib.infra.hosts import hosts_by_filter
from ocflib.infra.hosts import type_of_host


class TestHostsByFilter:

    def _hostnames(self, results):
        return [entry['cn'][0] for entry in results]

    @pytest.mark.parametrize('filter_str,expected', [
        ('(cn=death)', ['death']),
        ('(cn=doesnotexist)', []),
        ('(herp=derp)', []),
    ])
    def test_hosts_by_filter(self, filter_str, expected):
        results = self._hostnames(hosts_by_filter(filter_str))
        assert set(results) == set(expected)

    @pytest.mark.parametrize('filter_str', ['', 'cn=death', '42', 'asdf'])
    def test_invalid_filters(self, filter_str):
        with pytest.raises(Exception):
            hosts_by_filter(filter_str)

    def test_puppet_class(self):
        # This will break if death is ever renamed, but it's a useful test.
        #
        # We choose to test death because it is in lots of university DNS
        # records, so it is probably one of the more unlikely hosts to be
        # renamed.
        assert ('death' in
                self._hostnames(hosts_by_filter('(puppetClass=ocf_www)')))


@pytest.mark.parametrize('fqdn,expected', [
    ('death.ocf.berkeley.edu', 'death'),
    ('death', 'death'),
    ('', ''),
])
def test_hostname_from_domain(fqdn, expected):
    assert hostname_from_domain(fqdn) == expected

# This will similarly break if death or eruption are renamed.
#
# The former is unlikely, as explained above. The latter is less likely than
# any other desktop, since it is configured specially as the staff-only
# computer and the hostname will probably be reused when desktop machines are
# changed out.


@pytest.mark.parametrize('hostname,expected', [
    ('death.ocf.berkeley.edu', None),
    ('death', 'server'),
    ('eruption', 'desktop'),
    ('doesnotexist', None),
    ('', None),
])
def test_type_of_host(hostname, expected):
    assert type_of_host(hostname) == expected
