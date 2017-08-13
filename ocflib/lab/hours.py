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
import yaml

HOURS_SPREADSHEET = 'https://docs.google.com/spreadsheet/ccc?key=1WgczUrxqey63fmPRmdkCDMCbsfaTyCJrixiCeJj35UI&output=csv'  # noqa: E501
HOURS_FILE = '/home/s/st/staff/lab_hours.yaml'
HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/lab_hours.yaml'
SHIFT_LENGTH = timedelta(hours=0.5)


def _pull_hours():
    """download staff hours and save them to disk as YAML"""
    response = requests.get(HOURS_SPREADSHEET)
    response.raise_for_status()
    matrix = response.content.decode('utf-8').splitlines()
    matrix = [row.split(',') for row in matrix]

    # [1:] because the first box in the matrix is empty
    # matrix[0] = ['', 'Monday', 'Tuesday', ...]
    # row[0] = ['1:30PM-2:00PM', 'name1', 'name2', ...]
    shifts = [row[0] for row in matrix][1:]

    hours = {}

    for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
        hours[day] = {}
        for j, shift in enumerate(shifts):
            hours[day][shift] = matrix[j + 1][i + 1]  # person on shift

    # if this fails this should raise IOError anyways
    with open(HOURS_FILE, 'w') as hours_file:
        # pre-py3.6 dicts are unordered and this comes out ugly and confusing :(
        yaml.dump(hours, hours_file, default_flow_style=False)


def _load_hours():
    """load hours, from disk if available or web"""
    try:
        with open(HOURS_FILE, 'r') as hours_file:
            return yaml.safe_load(hours_file)
    except IOError:
        # fallback
        return yaml.safe_load(requests.get(HOURS_URL).text)


def _combine_shifts(shifts):
    """combine a days worth of shifts into a list of Hour() objects
       shifts = {'9:00AM-9:30AM': 'name1', '10:00AM-10:30AM': 'name2', ...}
    """
    raw_shifts = []
    for shift, staffer in shifts.items():
        if not staffer:
            continue

        open = datetime.strptime(shift, '%H:%M%p')  # 16:00PM
        close = open + SHIFT_LENGTH
        raw_shifts.append(Hour(open=open.time(), close=close.time(), staffer=staffer))

    raw_shifts.sort(key=lambda h: h.open)

    combined_shifts = []

    initial = raw_shifts[0]
    for next_shift in raw_shifts[1:]:
        if (initial.close in next_shift or next_shift.close in initial) and initial.staffer == next_shift.staffer:
            initial = Hour(open=min(initial.open, next_shift.open),
                           close=max(initial.close, next_shift.close),
                           staffer=initial.staffer)
        else:
            combined_shifts.append(initial)
            initial = next_shift

    combined_shifts.append(initial)  # capture tail ends where the last condition doesn't trip
    return combined_shifts


def _generate_regular_hours(force_refresh=False):
    if force_refresh:
        _pull_hours()

    raw_hours = _load_hours()

    combined_hours = {}

    for day in raw_hours:
        combined_hours[day] = _combine_shifts(raw_hours[day])

    return {i: combined_hours[day] for i, day in enumerate(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}


class Hour(namedtuple('Hours', ['open', 'close', 'staffer'])):

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


REGULAR_HOURS = _generate_regular_hours()


HOLIDAYS = [
    # start date, end date, holiday name, list of hours (date ranges are inclusive)
    (date(2017, 5, 13), date(2017, 8, 23), 'Summer Break', []),
    (date(2017, 9, 4), date(2017, 9, 4), 'Labor Day', []),
    (date(2017, 11, 10), date(2017, 11, 10), 'Veterans Day', []),
    (date(2017, 11, 22), date(2017, 11, 26), 'Thanksgiving Break', []),
    (date(2017, 12, 15), date(2017, 12, 15), 'Last Day Fall 2017', [Hour(time(9), time(12), 'test')]),
    (date(2017, 12, 16), date(2018, 1, 15), 'Winter Break', []),
    (date(2018, 2, 19), date(2018, 2, 19), 'Presidents\' Day', []),
    (date(2018, 3, 24), date(2018, 4, 1), 'Spring Break', []),
    (date(2017, 12, 15), date(2017, 12, 15), 'Last Day Fall 2017', [Hour(time(9), time(12), 'test')]),
    (date(2017, 12, 16), date(2017, 1, 16), 'Winter Break', []),
]
