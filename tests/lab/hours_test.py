import json
from datetime import date
from datetime import datetime
from datetime import time

import mock
import pytest
from freezegun import freeze_time

from ocflib.lab.hours import _generate_regular_hours
from ocflib.lab.hours import Day
from ocflib.lab.hours import Hour
from ocflib.lab.hours import REGULAR_HOURS

FAKE_HOLIDAYS = [
    (date(2015, 3, 14), date(2015, 3, 14), 'Pi Day', []),
    (date(2015, 3, 20), date(2015, 3, 22), 'Random 3 Days', [Hour(time(1), time(2), 'test')]),
]
FAKE_REGULAR_HOURS = {
    Day.MONDAY: [Hour(time(9), time(18), 'test')],
    Day.TUESDAY: [Hour(time(9), time(18), 'test')],
    Day.WEDNESDAY: [Hour(time(9, 10), time(18), 'test')],
    Day.THURSDAY: [Hour(time(9), time(18), 'test')],
    Day.FRIDAY: [Hour(time(9), time(18), 'test')],
    Day.SATURDAY: [Hour(time(11), time(18), 'test')],
    Day.SUNDAY: [Hour(time(12), time(17), 'test')],
}

FAKE_WEB_HOURS = json.loads('{"0": [["09:30:00", "14:00:00", "test1"], ["15:00:00", "15:30:00", "test2"]]}')


@pytest.fixture
def mock_hours_response():
    with mock.patch('ocflib.lab.hours.requests.get') as m:
        m.return_value.json.return_value = FAKE_WEB_HOURS
        yield


@pytest.fixture
def mock_hours():
    with mock.patch('ocflib.lab.hours.HOLIDAYS', FAKE_HOLIDAYS), \
            mock.patch('ocflib.lab.hours.REGULAR_HOURS', FAKE_REGULAR_HOURS):
        yield FAKE_HOLIDAYS, FAKE_REGULAR_HOURS


@pytest.fixture
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


def test_generate_regular_hours(mock_hours_response):
    hours = _generate_regular_hours()

    # hours[0] because FAKE_WEB_HOURS mocks Monday at index 0
    assert hours[0][0] == Hour(open=time(9, 30), close=time(14, 00), staffer='test1')
    assert hours[0][1] == Hour(open=time(15, 00), close=time(15, 30), staffer='test2')


class TestDay:

    @pytest.mark.parametrize('when,weekday,holiday,hours', [
        (date(2015, 3, 15), 'Sunday', None, [Hour(time(12), time(17), 'test')]),
        (datetime(2015, 3, 15), 'Sunday', None, [Hour(time(12), time(17), 'test')]),
        (datetime(2015, 3, 18), 'Wednesday', None, [Hour(time(9, 10), time(18), 'test')]),
        (datetime(2015, 3, 14), 'Saturday', 'Pi Day', []),
        (date(2015, 3, 22), 'Sunday', 'Random 3 Days', [Hour(time(1), time(2), 'test')]),
        (None, 'Saturday', None, [Hour(time(11), time(18), 'test')]),
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
