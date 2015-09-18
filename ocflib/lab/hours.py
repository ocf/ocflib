"""Methods for dealing with OCF lab hours.

For simplicity, we assume each day has one set of hours, and that they are
contiguous (e.g. 9am-5pm). We don't support breaks in the middle or other weird
hours.

All times are assumed to be OST (OCF Standard Time).
"""
from collections import defaultdict
from collections import namedtuple
from datetime import date
from datetime import datetime

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6
REGULAR_HOURS = defaultdict(lambda: (9, 18), {
    SUNDAY: (12, 17),
    SATURDAY: (11, 18),
})
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


class DayHours(namedtuple('DayHours', ['date', 'weekday', 'holiday', 'open', 'close'])):

    @classmethod
    def from_date(cls, when=None):
        if not when:
            when = date.today()

        if isinstance(when, datetime):
            when = when.date()

        weekday = when.strftime('%A')  # e.g. 'Thursday'
        my_holiday = None
        my_hours = REGULAR_HOURS[when.weekday()]

        for start, end, name, hours in HOLIDAYS:
            if start <= when <= end:
                my_holiday = name
                my_hours = hours
                break

        return cls(
            date=when,
            weekday=weekday,
            holiday=my_holiday,
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
    DayHours('Thursday', None, None)
    """
    return DayHours.from_date(when)


def is_open(when=None):
    """Returns a boolean whether the lab is currently open."""
    return get_hours(when).is_open(when)
