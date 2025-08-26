from datetime import date
from datetime import datetime
from datetime import timedelta

from ocflib.lab.stats import list_desktops
from ocflib.lab.stats import semester_dates
from ocflib.lab.stats import UtilizationProfile


def test_list_desktops():
    desktops = list_desktops()
    assert 10 < len(desktops) < 50

    assert 'fred' in desktops
    assert 'bandit' in desktops

    assert 'death' not in desktops


def test_list_desktops_staff_only():
    desktops = list_desktops(public_only=True)
    assert 10 < len(desktops) < 50

    assert 'fred' in desktops

    assert 'death' not in desktops


def test_fast_slow_profiles_same():
    start = datetime(2015, 11, 23)
    end = start + timedelta(days=1)

    slow_profiles = {
        host + '.ocf.berkeley.edu': UtilizationProfile.from_hostname(host, start, end)
        for host in list_desktops()
    }
    fast_profiles = UtilizationProfile.from_hostnames(list_desktops(), start, end)

    assert set(slow_profiles.keys()) == set(fast_profiles.keys())

    for host in slow_profiles.keys():
        slow = slow_profiles[host]
        fast = fast_profiles[host]

        assert slow.hostname == fast.hostname
        assert slow.start == fast.start
        assert slow.end == fast.end
        assert slow.sessions == fast.sessions


def test_semester_dates():
    assert semester_dates() is not None
    assert semester_dates(date(2016, 1, 1)) == (date(2016, 1, 1), date(2016, 7, 31))
    assert semester_dates(date(2017, 12, 30)) == (date(2017, 8, 1), date(2017, 12, 31))
