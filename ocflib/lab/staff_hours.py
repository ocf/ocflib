from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import timedelta
from hashlib import md5
from itertools import chain
from urllib.parse import urlencode

import requests
import yaml
from dateutil.parser import parse
from freezegun import freeze_time

from ocflib.account.search import user_attrs
from ocflib.account.utils import is_staff
from ocflib.lab.hours import Day
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/home/s/st/staff/staff_hours_example_vaibhav.yaml'
STAFF_HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/staff_hours.yaml'
StaffDay = namedtuple('StaffDay', ['day', 'hours', 'holiday'])
Hour = namedtuple('Hour', ['day', 'time', 'staff', 'cancelled'])

DAY_TO_NUM = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
              'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}


class Staffer(namedtuple('Staffer', ['user_name', 'real_name', 'position'])):
    def gravatar(self, size=100):
        email = email_for_user(self.user_name, check_exists=False)
        return 'https://www.gravatar.com/avatar/{hash}?{params}'.format(
            hash=md5(email.lower().encode('utf-8')).hexdigest(),
            params=urlencode({'d': 'mm', 's': size}),
        )


def _load_staff_hours():
    """Load staff hours, either from disk (if available) or HTTP."""
    try:
        with open(STAFF_HOURS_FILE) as f:
            return yaml.safe_load(f)
    except IOError:
        # fall back to loading from web
        return yaml.safe_load(requests.get(STAFF_HOURS_URL).text)


def date_is_holiday(name_of_day, time=datetime.now()):
    """Checks if name_of_day in the current week (not the next 7 days)
    is a holiday. Thus if name_of_day = Monday, and today is any day Tuesday thru Saturday,
    then this will determine if the past Monday is a holiday.
    However, if today were a Sunday, it will show the next Monday (which would be tomorrow)."""
    with freeze_time(time):
        today = date.today()
        # modded_day allows for time delta to be negative in order to find past name_of_day
        modded_day = today.isoweekday() % DAY_TO_NUM['Sunday']
        possible_holiday = Day.from_date(today + timedelta(days=DAY_TO_NUM[name_of_day] - modded_day))
    return possible_holiday.holiday


def get_staff_hours():
    """Returns a list where each index contains the staff hours
    for a day of the week (represented by the named tuple StaffDay)."""
    week = []
    staff_hours = _load_staff_hours()

    hour_info = staff_hours['staff-hours']
    for staff_day in hour_info:
        hours_for_day = get_staff_hours_per_day(hour_info[staff_day],
                                                staff_hours, staff_day)
        my_holiday = date_is_holiday(staff_day)
        week.append(
            StaffDay(day=staff_day,
                     hours=hours_for_day,
                     holiday=my_holiday)
        )
    return sorted(week,
                  key=lambda staff_day: DAY_TO_NUM[staff_day.day])


def get_staff_hours_per_day(day, staff_hours, name_of_day):

    def position(uid):
        if uid in staff_hours['staff-positions']:
            return staff_hours['staff-positions'][uid]
        elif is_staff(uid, group='ocfroot'):
            return 'Technical Manager'
        else:
            return 'Staff Member'

    # sorts staff hours within a day based on the starting time
    return sorted([
        Hour(day=name_of_day, time=hour,
             staff=[
                 Staffer(
                     user_name=attrs['uid'][0],
                     real_name=_remove_middle_names(attrs['cn'][0]),
                     position=position(attrs['uid'][0]),
                 ) for attrs in map(user_attrs, day[hour]['staff'])
             ],
             cancelled=day[hour]['cancelled'] or
             date_is_holiday(name_of_day) is not None,
             ) for hour in day],
        key=lambda hour: parse(hour.time[:hour.time.find('-')]))


def _remove_middle_names(name):
    names = name.split(' ')
    return names[0] + ' ' + names[-1]


def sort_hours(hour, time):
    ''' calcuates hour relative to given time'''
    with freeze_time(time):
        end_of_staff_hr = hour.time[hour.time.find('-') + 1:]
        time_diff = parse(hour.day + end_of_staff_hr) - time
        if (time_diff < timedelta(0)):
            time_diff = timedelta.max
    return time_diff


def get_staff_hours_soonest_first(time=datetime.now()):
    """Sorts Staff hours relative to the current time.
    Filters out staff hours that are cancelled or on holiday."""

    hours = chain.from_iterable([staff_day.hours for staff_day in get_staff_hours()])
    hours = sorted(hours, key=lambda hour: sort_hours(hour, time))

    hours = [hour for hour in hours if not hour.cancelled]
    hours_with_no_cancelled_hours = [hour for hour in hours if not date_is_holiday(hour.day)]
    return(hours_with_no_cancelled_hours)
