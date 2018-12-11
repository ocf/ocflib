"""Methods for dealing with OCF lab hours.

All times are assumed to be OST (OCF Standard Time).

Usage:

    >>> from ocflib.lab.hours import Day
    >>> Day.from_date(date(2015, 10, 12))
    Day(
        date=datetime.date(2015, 10, 12),
        weekday='Monday',
        holiday=None,
        hours=[Hour(open=9, close=21)],
    )
"""
from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

import requests

HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/hours_temp'


def _generate_regular_hours():
    """pull hours from ocfweb and return them in the manner expected by Day().

    The canonical source of OCF lab hours is a Google Spreadsheet. Parsing
    that sheet is handled by the ocfweb API. This function is a shim for code
    that expects hours to come from ocflib, where they were originally
    hardcoded.

    >>> _generate_regular_hours()
    {
        Day.MONDAY: [Hour(time(11, 10), time(13), 'staff1'),
                     Hour(time(14, 10), time(18), 'staff2'),
                     ...],
        Day.TUESDAY: ...
        ...
    }
    """

    regular_hours = {}

    for day, hours in requests.get(HOURS_URL, timeout=20).json().items():
        regular_hours[int(day)] = [
            Hour(
                open=_parsetime(hour[0]),
                close=_parsetime(hour[1]),
                staffer=hour[2],
            )
            for hour in hours
        ]

    return regular_hours


def _parsetime(t):
    return datetime.strptime(t, '%H:%M:%S').time()


class Hour:

    def __init__(self, open, close, staffer=None):
        self.open = open
        self.close = close
        self.staffer = staffer

    def __contains__(self, when):
        if isinstance(when, datetime):
            when = when.time()
        return self.open <= when < self.close

    def __eq__(self, other):
        return self.open == other.open and \
            self.close == other.close and \
            self.staffer == other.staffer


class Day(namedtuple('Day', ['date', 'weekday', 'holiday', 'hours'])):

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_date(cls, when=None):
        """Return whether a Day representing the given day.

        If not provided, when defaults to today.
        """
        if not when:
            when = date.today()

        if isinstance(when, datetime):
            when = when.date()

        # check if it's a holiday
        my_holiday = None
        my_hours = _generate_regular_hours()[when.weekday()]

        for start, end, name, hours in HOLIDAYS:
            if start <= when <= end:
                my_holiday = name
                my_hours = hours
                break

        return cls(
            date=when,
            weekday=when.strftime('%A'),
            holiday=my_holiday,
            hours=my_hours,
        )

    def is_open(self, when=None):
        """Return whether the lab is open at the given time.

        If not provided, when defaults to now.
        """
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.date != when.date():
            raise ValueError('{} is on a different day than {}'.format(when, self))

        return any(when in hour for hour in self.hours)

    def time_to_open(self, when=None):
        """Return timedelta object representing time until the lab is open from the given time.

        If not provided, defaults to now"""
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.date != when.date():
            raise ValueError('{} is on a different day than {}'.format(when, self))

        if self.is_open(when=when):
            return timedelta()

        def date_opens(date):
            return [datetime.combine(date, h.open) for h in Day.from_date(date).hours]
        opens = date_opens(self.date)
        # because we assume when is in the current day, any hours in future dates don't need to be filtered
        opens = [o for o in opens if o > when]
        date = self.date
        while not opens:
            date += timedelta(days=1)
            opens = date_opens(date)

        return opens[0] - when

    def time_to_close(self, when=None):
        """Return timedelta object representing time until the lab is closed from the given time.

        If not provided, defaults to now"""
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.date != when.date():
            raise ValueError('{} is on a different day than {}'.format(when, self))

        # because hour intervals should not overlap this should be length 0 or 1
        hours = [hour for hour in self.hours if when in hour]
        if not hours:
            return timedelta()
        return datetime.combine(self.date, hours[0].close) - when

    @property
    def closed_all_day(self):
        return not self.hours


HOLIDAYS = [
    # start date, end date, holiday name, list of hours (date ranges are inclusive)
    (date(2018, 2, 1), date(2018, 2, 1), 'Early Lab Closure', [Hour(time(9), time(19))]),
    (date(2018, 2, 4), date(2018, 2, 4), 'Early Lab Closure', [Hour(time(9), time(15))]),
    (date(2018, 2, 19), date(2018, 2, 19), 'Presidents\' Day', []),
    (date(2018, 3, 3), date(2018, 3, 3), 'Early Lab Closure', [Hour(time(9), time(12))]),
    (date(2018, 3, 24), date(2018, 4, 1), 'Spring Break', []),
    (date(2018, 5, 12), date(2018, 8, 21), 'Summer Break', []),
    (date(2018, 9, 1), date(2018, 9, 3), 'Labor Day', []),
    (date(2018, 9, 12), date(2018, 9, 12), 'Early Lab Closure', [Hour(time(9), time(19))]),
    (date(2018, 9, 18), date(2018, 9, 18), 'Early Lab Closure', [Hour(time(9), time(17))]),
    (date(2018, 9, 19), date(2018, 9, 19), 'Early Lab Closure', [Hour(time(9), time(19))]),
    (date(2018, 11, 10), date(2018, 11, 10), 'OCF Hackathon', []),
    (date(2018, 11, 11), date(2018, 11, 11), 'Veterans Day Weekend', []),
    (date(2018, 11, 12), date(2018, 11, 12), 'Veterans Day Weekend', []),
    (date(2018, 11, 15), date(2018, 11, 15), 'Early Lab Closure', [Hour(time(9), time(18))]),
    (date(2018, 11, 16), date(2018, 11, 20), 'Campus AQI Closure', []),
    (date(2018, 11, 21), date(2018, 11, 25), 'Thanksgiving Break', []),
    (date(2018, 12, 3), date(2018, 12, 3), 'Late Lab Opening', [Hour(time(10), time(18))]),
    (date(2018, 12, 14), date(2018, 12, 14), 'Last Day of Finals', [Hour(time(9), time(14))]),
    (date(2018, 12, 15), date(2019, 1, 14), 'Winter Break', []),
]
