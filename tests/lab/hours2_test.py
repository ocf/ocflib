from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

import pytest
from freezegun import freeze_time

from ocflib.lab.hours2 import Holiday
from ocflib.lab.hours2 import Hour
from ocflib.lab.hours2 import HoursListing
from ocflib.lab.hours2 import read_hours_listing
from ocflib.lab.hours2 import Weekday


FAKE_HOURS_YAML = '''
regular:
  Monday:
    - ['9:00', '18:00']
  Tuesday:
    - ['9:00', '18:00']
  Wednesday:
    - ['9:10', '18:00']
  Thursday:
    - ['9:00', '12:00']
    - ['14:00', '18:00']
  Friday:
    - ['9:00', '18:00']
  Saturday:
    - ['11:00', '18:00']
  Sunday:
    - ['12:00', '17:00']
holidays:
  - date: 2015-03-14
    reason: Pi Day
  - date: [2015-03-20, 2015-03-22]
    reason: Random 3 Days
    hours:
      - ['1:00', '2:00']
  - date: [2015-12-19, 2016-01-18]
    reason: Winter Break
'''

EMPTY_REGULAR_HOURS = dict(zip(Weekday, [[]] * 7))
FAKE_NOW = datetime(2015, 8, 22, 14, 11)


@pytest.fixture
def mock_hours_yaml(fs):
    fs.create_file('/etc/ocf/hours.yaml', contents=FAKE_HOURS_YAML)


@pytest.fixture
def mock_now():
    with freeze_time(FAKE_NOW):
        yield


@pytest.mark.parametrize('now,expected_hours', [
    # regular hours
    (date(2015, 3, 13), [Hour(open=time(9), close=time(18))]),
    (None, [Hour(open=time(11), close=time(18))]),

    # holidays
    (date(2015, 3, 14), []),
    (date(2015, 3, 19), [
        Hour(open=time(9), close=time(12)),
        Hour(open=time(14), close=time(18)),
    ]),
    (date(2015, 3, 20), [Hour(open=time(1), close=time(2))]),
    (date(2015, 3, 21), [Hour(open=time(1), close=time(2))]),
    (date(2015, 3, 22), [Hour(open=time(1), close=time(2))]),
    (date(2015, 3, 23), [Hour(open=time(9), close=time(18))]),
])
def test_hours_on_date(now, expected_hours, mock_hours_yaml, mock_now):
    assert read_hours_listing().hours_on_date(now) == expected_hours


@pytest.mark.parametrize('now,expected_open', [
    # regular hours
    (datetime(2015, 3, 15, 12), True),
    (datetime(2015, 3, 19, 17), True),
    (datetime(2015, 3, 19, 9), True),
    (datetime(2015, 3, 19, 18), False),
    (datetime(2015, 3, 19, 0), False),
    (None, True),

    # holidays
    (datetime(2015, 3, 14, 12), False),
    (datetime(2015, 3, 14, 0), False),
    (datetime(2015, 3, 20, 0), False),
    (datetime(2015, 3, 20, 1), True),
    (datetime(2015, 3, 20, 1, 30), True),
    (datetime(2015, 3, 20, 1, 59), True),
    (datetime(2015, 3, 20, 2, 0), False),
])
def test_is_open(now, expected_open, mock_hours_yaml, mock_now):
    assert read_hours_listing().is_open(now) == expected_open


@pytest.mark.parametrize('now,expected_next_open', [
    (datetime(2015, 1, 5, 8), datetime(2015, 1, 5, 9)),
    (datetime(2015, 1, 6, 19), datetime(2015, 1, 7, 9, 10)),
    (datetime(2015, 1, 8, 8), datetime(2015, 1, 8, 9)),
    (datetime(2015, 1, 8, 13), datetime(2015, 1, 8, 14)),
    (datetime(2015, 1, 8, 19), datetime(2015, 1, 9, 9)),

    # Pi Day
    (datetime(2015, 3, 13, 19), datetime(2015, 3, 15, 12)),
    (datetime(2015, 3, 14, 9), datetime(2015, 3, 15, 12)),
    (datetime(2015, 3, 14, 12), datetime(2015, 3, 15, 12)),
    (datetime(2015, 3, 14, 19), datetime(2015, 3, 15, 12)),

    # Random 3 Days
    (datetime(2015, 3, 19, 19), datetime(2015, 3, 20, 1)),
    (datetime(2015, 3, 20, 0), datetime(2015, 3, 20, 1)),
    (datetime(2015, 3, 20, 3), datetime(2015, 3, 21, 1)),
    (datetime(2015, 3, 22, 3), datetime(2015, 3, 23, 9)),

    # Winter Break
    (datetime(2015, 12, 18, 21), datetime(2016, 1, 19, 9)),
    (datetime(2015, 12, 19, 12), datetime(2016, 1, 19, 9)),
    (datetime(2016, 1, 18, 12), datetime(2016, 1, 19, 9)),

    # Far in the future
    (datetime(2500, 3, 1, 21), datetime(2500, 3, 2, 9)),
])
def test_time_to_open(now, expected_next_open, mock_hours_yaml):
    hours_listing = read_hours_listing()
    assert hours_listing.time_to_open(now) == expected_next_open - now
    assert hours_listing.time_to_close(now) == timedelta()


@pytest.mark.parametrize('now,expected_next_close', [
    (datetime(2015, 1, 5, 10), datetime(2015, 1, 5, 18)),
    (datetime(2015, 1, 8, 10), datetime(2015, 1, 8, 12)),
    (datetime(2015, 1, 8, 15), datetime(2015, 1, 8, 18)),

    # Random 3 Days
    (datetime(2015, 3, 20, 1, 30), datetime(2015, 3, 20, 2)),

    # Far in the future
    (datetime(2500, 3, 1, 10), datetime(2500, 3, 1, 18)),
])
def test_time_to_close(now, expected_next_close, mock_hours_yaml):
    hours_listing = read_hours_listing()
    assert hours_listing.time_to_close(now) == expected_next_close - now
    assert hours_listing.time_to_open(now) == timedelta()


def test_time_to_close_now(mock_hours_yaml, mock_now):
    hours_listing = read_hours_listing()
    assert hours_listing.time_to_open() == timedelta()
    assert hours_listing.time_to_close() == datetime(2015, 8, 22, 18) - FAKE_NOW


def test_no_hours():
    # Pray that this never comes to pass 🙏🙏🙏
    hours_listing = HoursListing(regular=EMPTY_REGULAR_HOURS, holidays=[])
    assert hours_listing.time_to_close() == timedelta()
    assert hours_listing.time_to_open() is None


@pytest.mark.parametrize('startdate,enddate,hours', [
    (date(2015, 2, 3), date(2015, 2, 2), []),
    (
        date(2015, 2, 2),
        date(2015, 2, 3),
        [Hour(time(10), time(12)), Hour(time(11), time(14))],
    ),
    (
        date(2015, 2, 2),
        date(2015, 2, 3),
        [Hour(time(10), time(12)), Hour(time(8), time(14))],
    ),
    (
        date(2015, 2, 2),
        date(2015, 2, 3),
        [Hour(time(10), time(12)), Hour(time(8), time(9))],
    ),
])
def test_invalid_holiday(startdate, enddate, hours):
    with pytest.raises(ValueError):
        Holiday(reason='', startdate=startdate, enddate=enddate, hours=hours)


def test_idempotence(mock_hours_yaml):
    hours_listing = read_hours_listing()
    assert hours_listing == HoursListing(**vars(hours_listing))
