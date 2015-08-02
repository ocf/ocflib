import pytest

from ocflib.infra.hosts import hosts_by_filter


class TestHostsByFilter:

    def _hostnames(self, results):
        return [entry['cn'][0] for entry in results]

    @pytest.mark.parametrize('filter_str,expected', [
        ('(cn=death)', ['death']),
        ('(cn=doesnotexist)', []),
        ('(herp=derp)', []),
    ])
    def test_users_by_filter(self, filter_str, expected):
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
