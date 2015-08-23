"""Methods for dealing with OCF lab hours.

For simplicity, we assume each day has one set of hours, and that they are
contiguous (e.g. 9am-5pm). We don't support breaks in the middle or other weird
hours.

All times are assumed to be OST (OCF Standard Time).
"""
from collections import namedtuple
from datetime import date
from datetime import datetime


REGULAR_HOURS = {
    0: (9, 18),  # Monday
    1: (9, 18),  # Tuesday
    2: (9, 18),  # Wednesday
    3: (9, 18),  # Thursday
    4: (9, 18),  # Friday
    5: (11, 18),  # Saturday
    6: (12, 17),  # Sunday
}

HOLIDAYS = {
    # start date, end date, holiday name, hours (date ranges are inclusive)
    (date(2015, 8, 1), date(2015, 8, 25), 'Summer Break', (None, None)),
    (date(2015, 9, 7), date(2015, 9, 7), 'Labor Day', (None, None)),
    (date(2015, 11, 11), date(2015, 11, 11), 'Veteran\'s Day', (None, None)),
    (date(2015, 11, 24), date(2015, 11, 24), 'Thanksgiving Break', (9, 12)),
    (date(2015, 11, 25), date(2015, 11, 27), 'Thanksgiving Break', (None, None)),
    (date(2015, 12, 7), date(2015, 12, 13), 'R.R.R. Week', (11, 21)),
    (date(2015, 12, 14), date(2015, 12, 17), 'Finals Week', (9, 21)),
    (date(2015, 12, 18), date(2015, 12, 18), 'Last Day Fall 2015', (9, 12)),
}


class DayHours(namedtuple('DayHours', ['name', 'open', 'close'])):

    @classmethod
    def from_date(cls, when=None):
        if not when:
            when = date.today()

        if isinstance(when, datetime):
            when = when.date()

        my_name = when.strftime('%A')  # e.g. 'Thursday'
        my_hours = REGULAR_HOURS[when.weekday()]

        for start, end, name, hours in HOLIDAYS:
            if start <= when <= end:
                my_name = '{} ({})'.format(name, my_name)
                my_hours = hours
                break

        return cls(
            name=my_name,
            open=my_hours[0],
            close=my_hours[1],
        )

    def is_open(self, when=None):
        if not when:
            when = datetime.now()

        if not isinstance(when, datetime):
            raise ValueError('{} must be a datetime instance'.format(when))

        if None in [self.open, self.close]:
            return False

        return self.open <= when.hour < self.close


def get_hours(when=None):
    """Return a DayHours object representing the day's hours.

    >>> get_hours()
    DayHours('Thursday', 9, 18)

    >>> get_hours()
    DayHours('Thanksgiving Break (Thursday)', None, None)
    """
    return DayHours.from_date(when)


def is_open(when=None):
    """Returns a boolean whether the lab is currently open."""
    return get_hours(when).is_open(when)
