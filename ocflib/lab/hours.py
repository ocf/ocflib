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
from collections import defaultdict
from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

import requests

SHIFT_LENGTH = timedelta(hours=1)
SHIFTS_URL = 'https://docs.google.com/spreadsheet/ccc?key=1WgczUrxqey63fmPRmdkCDMCbsfaTyCJrixiCeJj35UI&output=csv'
DAY_OFFSET = 1


class Hour(namedtuple('Hours', ['open', 'close'])):

    def __contains__(self, when):
        if isinstance(when, time):
            return self.open <= when < self.close
        return self.open <= when.time() < self.close


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
        my_hours = REGULAR_HOURS[when.weekday()]

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


def _shift_from_start(start):
    """Returns an Hour object from the start time"""
    end = (datetime.combine(date.today(), start) + SHIFT_LENGTH).time()
    return Hour(start, end)


def _string_to_time(when):
    return datetime.strptime(when, '%I:%M %p').time()


def _shift_matrix():
    """Returns the OCF staff shifts from google spreadsheet
    as a 2-D matrix"""
    response = requests.get(SHIFTS_URL)
    content = response.content.decode('utf-8').splitlines()
    return [row.split(',') for row in content]


def get_shifts(when=None):
    """Fetches lab shifts for given datetime instance or weekday int."""
    if when is None:
        when = datetime.now()

    shifts = _shift_matrix()[1:]
    try:
        return [_shift_from_start(_string_to_time(hour[0]))
                for hour in shifts if hour[when.weekday() + DAY_OFFSET]]
    except AttributeError:
        return [_shift_from_start(_string_to_time(hour[0]))
                for hour in shifts if hour[when + DAY_OFFSET]]


def union(shift1, shift2):
    """
    Returns the combined Hour if there is an overlap,
    otherwise, return None
    """
    if shift1.close in shift2 or shift2.close in shift1:
        return Hour(min(shift1.open, shift1.open),
                    max(shift1.close, shift2.close))
    else:
        return None


def get_hours(when=None):
    """Combines lab shifts as much as possible and returns the final list of Hours for
    'day'.  'day' is an int [0,6] or datetime object"""
    if when is None:
        when = datetime.now()

    shifts = get_shifts(when)
    i = 0
    while i < len(shifts):
        j = i + 1
        while j < len(shifts):
            hour = union(shifts[i], shifts[j])
            if hour is not None:
                shifts.pop(j)
                shifts[i] = hour
            else:
                j += 1
        i += 1
    return shifts


def staff_on_shift(when=None):
    """Finds the staffer on shift during 'when' according to
    google spreadsheet.  Returns None if no staffer found.
    'when' is a datetime object.

    Does not support holiday hours/shifts.
    """
    if when is None:
        when = datetime.now()

    shifts = _shift_matrix()[1:]
    for hour in shifts:
        if when in _shift_from_start(
                _string_to_time(hour[0])):
            return hour[when.weekday() + DAY_OFFSET]


REGULAR_HOURS = defaultdict(lambda: [Hour(time(9), time(19))], {
    Day.MONDAY: [Hour(time(9, 10), time(18))],
    Day.TUESDAY: [Hour(time(9, 10), time(20))],
    Day.WEDNESDAY: [Hour(time(9, 10), time(22))],
    Day.THURSDAY: [Hour(time(9, 10), time(20))],
    Day.FRIDAY: [Hour(time(9, 10), time(18))],
    Day.SATURDAY: [Hour(time(11, 10), time(19))],
    Day.SUNDAY: [Hour(time(11, 10), time(19))],
})

HOLIDAYS = [
    # start date, end date, holiday name, list of hours (date ranges are inclusive)
    (date(2017, 5, 13), date(2017, 8, 22), 'Summer Break', []),
    (date(2017, 9, 4), date(2017, 9, 4), 'Labor Day', []),
    (date(2017, 11, 10), date(2017, 11, 10), 'Veterans Day', []),
    (date(2017, 11, 22), date(2017, 11, 26), 'Thanksgiving Break', []),
    (date(2017, 12, 15), date(2017, 12, 15), 'Last Day Fall 2017', [Hour(time(9), time(12))]),
    (date(2017, 12, 16), date(2018, 1, 15), 'Winter Break', []),
    (date(2018, 2, 19), date(2018, 2, 19), 'Presidents\' Day', []),
    (date(2018, 3, 24), date(2018, 4, 1), 'Spring Break', []),
]
