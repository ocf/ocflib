from datetime import date
from datetime import datetime
from datetime import time

import mock
import pytest
from freezegun import freeze_time

from ocflib.lab.hours import Day
from ocflib.lab.hours import Hour
from ocflib.lab.hours import REGULAR_HOURS


FAKE_HOLIDAYS = [
    (date(2015, 3, 14), date(2015, 3, 14), 'Pi Day', []),
    (date(2015, 3, 20), date(2015, 3, 22), 'Random 3 Days', [Hour(time(1), time(2))]),
]
FAKE_REGULAR_HOURS = {
    Day.MONDAY: [Hour(time(9), time(18))],
    Day.TUESDAY: [Hour(time(9), time(18))],
    Day.WEDNESDAY: [Hour(time(9, 10), time(18))],
    Day.THURSDAY: [Hour(time(9), time(18))],
    Day.FRIDAY: [Hour(time(9), time(18))],
    Day.SATURDAY: [Hour(time(11), time(18))],
    Day.SUNDAY: [Hour(time(12), time(17))],
}


@pytest.yield_fixture
def mock_hours():
    with mock.patch('ocflib.lab.hours.HOLIDAYS', FAKE_HOLIDAYS), \
            mock.patch('ocflib.lab.hours.REGULAR_HOURS', FAKE_REGULAR_HOURS):
        yield FAKE_HOLIDAYS, FAKE_REGULAR_HOURS


@pytest.yield_fixture
def mock_today():
    with freeze_time('2015-08-22 14:11:00'):
        yield


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
def test_is_open(now, expected_open, mock_hours, mock_today):
    assert Day.from_date(now).is_open(now) == expected_open


def test_is_open_fails_with_just_date():
    with pytest.raises(ValueError):
        Day.from_date().is_open(date(2015, 3, 14))


class TestDay:

    @pytest.mark.parametrize('when,weekday,holiday,hours', [
        (date(2015, 3, 15), 'Sunday', None, [Hour(time(12), time(17))]),
        (datetime(2015, 3, 15), 'Sunday', None, [Hour(time(12), time(17))]),
        (datetime(2015, 3, 18), 'Wednesday', None, [Hour(time(9, 10), time(18))]),
        (datetime(2015, 3, 14), 'Saturday', 'Pi Day', []),
        (date(2015, 3, 22), 'Sunday', 'Random 3 Days', [Hour(time(1), time(2))]),
        (None, 'Saturday', None, [Hour(time(11), time(18))]),
    ])
    def test_creation(self, mock_hours, mock_today, when, weekday, holiday, hours):
        day_hours = Day.from_date(when)
        if when:
            if isinstance(when, datetime):
                day = when.date()
            else:
                day = when
        else:
            day = date.today()

        assert day_hours.date == day
        assert day_hours.weekday == weekday
        assert day_hours.hours == hours
        assert day_hours.holiday == holiday


@pytest.mark.parametrize('day', [
    Day.SUNDAY,
    Day.MONDAY,
    Day.TUESDAY,
    Day.WEDNESDAY,
    Day.THURSDAY,
    Day.FRIDAY,
    Day.SATURDAY,
])
def test_hours(day):
    hours = REGULAR_HOURS[day]
    assert isinstance(hours, list)
    assert len(hours) >= 1

    for hour in hours:
        assert isinstance(hour.open, time)
        assert isinstance(hour.close, time)
