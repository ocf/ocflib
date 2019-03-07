"""Methods for dealing with OCF lab hours.

All times are assumed to be OST (OCF Standard Time).

Usage:

    >>> from ocflib.lab.hours2 import read_hours_listing()
    >>> hours_listing = read_hours_listing()
    >>> hours_listing.hours_on_date(date(2015-10-12))
    [Hour(open=datetime.time(9, 0), close=datetime.time(18, 0))]
"""
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from enum import IntEnum

import attr
import yaml


class Weekday(IntEnum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


def _parsetime(t):
    if isinstance(t, time):
        return t

    return datetime.strptime(t, '%H:%M').time()


def _parse_regular_hours(regular):
    """Parses a dictionary of regular hours, as used in the yaml file.

    Keys can be either weekday strings ("Monday", "Tuesday", ...) or Weekday
    enums. Values should be a list of timeranges, parseable by
    _parse_hours_list.
    """
    out = {}
    for weekday, hours in regular.items():
        if isinstance(weekday, int):
            weekday = Weekday(weekday)
        else:
            # Convert strings ('Monday') to int (0)
            weekday = Weekday[weekday]

        out[weekday] = _parse_hours_list(hours)

    if out.keys() != set(Weekday):
        raise ValueError('Regular hours must be set for all weekdays')

    return out


def _parse_hours_list(time_ranges):
    """Converts a list of timeranges to a list of Hour objects.

    This function idempotently does nothing on a list of Hour objects.

    Raises an ValueError if the timeranges overlap or are out of order.

    >>> _parse_hours_list([['8:30', '10:00'], ['11:00', '3:00']])
    [Hour(time(8, 30), time(10)), Hour(time(11), time(3))]

    >>> _parse_hours_list([['8:30', '10:00'], ['9:00', '11:00']])
    Traceback (most recent call last):
        ...
    ValueError: Hours must be in order

    >>> _parse_hours_list([['8:30', '10:00'], ['8:00', '11:00']])
    Traceback (most recent call last):
        ...
    ValueError: Hours must be in order
    """
    hours = []

    for hour in time_ranges:
        if not isinstance(hour, Hour):
            hour = Hour(hour[0], hour[1])

        if hours and hours[-1].close > hour.open:
            raise ValueError('Hours must be in order')

        hours.append(hour)

    return hours


def _parse_holiday(holiday):
    """Converts a holiday dict to a Holiday object.

    This function idempotently does nothing on a Holiday object.
    """
    if isinstance(holiday, Holiday):
        return holiday

    if isinstance(holiday['date'], list):
        start, end = holiday['date']
    elif isinstance(holiday['date'], date):
        start = end = holiday['date']
    else:
        raise ValueError(
            'Holiday date is not a [start, end] pair or single datetime'
        )

    return Holiday(
        reason=holiday['reason'],
        startdate=start,
        enddate=end,
        hours=holiday.get('hours', []),
    )


def _parse_holiday_list(holidays):
    """Converts a list of holiday dicts to a list of Holiday objects.

    This function idempotently does nothing on a list of Holiday objects.

    Raises a ValueError if the dateranges overlap.
    """
    out = []

    for holiday in holidays:
        holiday = _parse_holiday(holiday)
        if out and out[-1].enddate >= holiday.startdate:
            raise ValueError('Holiday dateranges must not overlap')

        out.append(holiday)

    return out


@attr.s(frozen=True)
class HoursListing:
    regular = attr.ib(converter=_parse_regular_hours)
    holidays = attr.ib(converter=_parse_holiday_list)

    def hours_on_date(self, when=None):
        """Returns the hours on the given date.

        If not provided, when defaults to today.
        """
        if when is None:
            when = date.today()

        if not isinstance(when, date):
            raise ValueError('{} must be a datetime instance'.format(when))

        # check if it's a holiday
        for holiday in self.holidays:
            if holiday.startdate <= when <= holiday.enddate:
                return holiday.hours

        return self.regular[when.weekday()]

    def is_open(self, when=None):
        """Return whether the lab is open at the given datetime.

        If not provided, when defaults to now.
        """
        if when is None:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        return any(
            when.time() in hour
            for hour in self.hours_on_date(when.date())
        )

    def time_to_open(self, when=None):
        """Return timedelta object representing time until the lab is open from the given datetime.

        If the lab will never be open, returns None.

        If not provided, when defaults to now.
        """
        if when is None:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if self.is_open(when=when):
            return timedelta()

        on_date = when.date()

        # Loop until the end of the last holiday plus 8 days
        if self.holidays:
            last_holiday = self.holidays[-1].enddate
        else:
            last_holiday = on_date

        while on_date < max(when.date(), last_holiday) + timedelta(days=8):
            future_hours = self.hours_on_date(on_date)
            for hour in future_hours:
                time_to_open = datetime.combine(on_date, hour.open) - when
                if time_to_open >= timedelta():
                    return time_to_open

            on_date += timedelta(days=1)

        return None

    def time_to_close(self, when=None):
        """Return timedelta object representing time until the lab is closed from the given datetime.

        If the lab will never close, returns None.

        If not provided, when defaults to now.
        """
        if when is None:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if not self.is_open(when=when):
            return timedelta()

        on_date = when.date()

        # Loop until the end of the last holiday plus 8 days
        if self.holidays:
            last_holiday = self.holidays[-1].enddate
        else:
            last_holiday = on_date

        while on_date < max(when.date(), last_holiday) + timedelta(days=8):
            future_hours = self.hours_on_date(on_date)
            for hour in future_hours:
                time_to_close = datetime.combine(on_date, hour.close) - when
                if time_to_close >= timedelta():
                    return time_to_close

            on_date += timedelta(days=1)

        return None


@attr.s(frozen=True)
class Holiday:
    reason = attr.ib(validator=[attr.validators.instance_of(str)])
    startdate = attr.ib(validator=[attr.validators.instance_of(date)])
    enddate = attr.ib(validator=[attr.validators.instance_of(date)])
    hours = attr.ib(converter=_parse_hours_list)

    @enddate.validator
    def _valid_enddate(self, attribute, value):
        if value < self.startdate:
            raise ValueError('Holiday dateranges must be valid')


@attr.s(frozen=True)
class Hour:
    open = attr.ib(
        validator=[attr.validators.instance_of(time)],
        converter=_parsetime,
    )
    close = attr.ib(
        validator=[attr.validators.instance_of(time)],
        converter=_parsetime,
    )

    def __contains__(self, when):
        if not isinstance(when, time):
            raise ValueError('{} must be a time instance'.format(when))
        return self.open <= when < self.close

    @close.validator
    def _valid_closetime(self, attribute, value):
        if value <= self.open:
            raise ValueError('Hour timerange must be valid')


def read_hours_listing():
    hours_config = yaml.safe_load(open('/etc/ocf/hours.yaml'))

    return HoursListing(**hours_config)
