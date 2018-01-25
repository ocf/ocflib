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

from ocflib.account.search import user_attrs
from ocflib.account.utils import is_staff
from ocflib.lab.hours import Day
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/home/s/st/staff/staff_hours_example_vaibhav.yaml'
STAFF_HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/staff_hours.yaml'
StaffDay = namedtuple('StaffDay', ['day', 'hours', 'holiday'])
Hour = namedtuple('Hour', ['day', 'time', 'staff', 'cancelled'])

string_to_constant = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
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


def date_is_holiday(name_of_day):
    """Checks if any of the days in the current week (not the next 7 days)
    are holidays. Thus if today is Friday, then this will determine if last Mon.
    is a holiday not next Monday. However, on Sunday, it will show the next Monday."""
    today = date.today()
    modded_day = today.isoweekday() % string_to_constant['Sunday']
    date_object = Day.from_date(today + timedelta(days=string_to_constant[name_of_day] - modded_day))
    return date_object.holiday


def get_staff_hours():
    """Returns a list where each index contains the staff hours
    for a day of the week (represented by the named tuple StaffDay)."""
    lst_of_staff_days = []
    staff_hours = _load_staff_hours()

    hour_info = staff_hours['staff-hours']
    for staff_day in hour_info:
        hours_for_day = get_staff_hours_per_day(hour_info[staff_day],
                                                staff_hours, staff_day)
        my_holiday = date_is_holiday(staff_day)
        lst_of_staff_days.append(
            StaffDay(day=staff_day,
                     hours=hours_for_day,
                     holiday=my_holiday)
        )
    return sorted(lst_of_staff_days,
                  key=lambda staff_day: string_to_constant[staff_day.day])


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


def sort_hours(hour):
    now = datetime.now()
    end_of_staff_hr = hour.time[hour.time.find('-') + 1:]
    time_diff = parse(hour.day + end_of_staff_hr) - now
    if (time_diff < timedelta(0)):
        time_diff = timedelta.max
    return time_diff


def get_staff_hours_soonest_first():
    """Sorts Staff hours relative to the current time.
    Filters out staff hours that are cancelled or on holiday."""

    hours = chain.from_iterable([staff_day.hours for staff_day in get_staff_hours()])
    hours = sorted(hours, key=lambda hour: sort_hours(hour))

    hours = [hour for hour in hours if not hour.cancelled]
    hours_with_no_cancelled_hours = [hour for hour in hours if not date_is_holiday(hour.day)]
    return(hours_with_no_cancelled_hours)
