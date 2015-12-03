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


class Hour(namedtuple('Hours', ['open', 'close'])):

    def __contains__(self, when):
        return self.open <= when.hour < self.close


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

        return any(when in hour for hour in self.hours)

    @property
    def closed_all_day(self):
        return not self.hours


REGULAR_HOURS = defaultdict(lambda: [Hour(9, 21)], {
    Day.FRIDAY: [Hour(9, 20)],
    Day.SATURDAY: [Hour(11, 19)],
    Day.SUNDAY: [Hour(11, 19)],
})

HOLIDAYS = [
    # start date, end date, holiday name, list of hours (date ranges are inclusive)
    (date(2015, 8, 1), date(2015, 8, 25), 'Summer Break', []),
    (date(2015, 9, 7), date(2015, 9, 7), 'Labor Day', []),
    (date(2015, 11, 11), date(2015, 11, 11), 'Veteran\'s Day', []),
    (date(2015, 11, 12), date(2015, 11, 12), 'Moving (Early Close)', [Hour(9, 18)]),
    (date(2015, 11, 13), date(2015, 11, 15), 'Moving', []),
    (date(2015, 11, 24), date(2015, 11, 24), 'Thanksgiving Break (Early Close)', [Hour(9, 18)]),
    (date(2015, 11, 25), date(2015, 11, 29), 'Thanksgiving Break', []),
    (date(2015, 12, 7), date(2015, 12, 7), 'Early Close - OCF Event', [Hour(9, 19)]),
    (date(2015, 12, 18), date(2015, 12, 18), 'Early Close - Last Day', [Hour(9, 20)]),
    (date(2015, 12, 19), date(2016, 1, 19), 'Winter Break', []),
]
