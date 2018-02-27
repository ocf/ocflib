from collections import namedtuple
from datetime import date
from datetime import datetime as dtime
from datetime import timedelta
from hashlib import md5
from itertools import chain
from urllib.parse import urlencode

import requests
import yaml

from ocflib.account.search import user_attrs
from ocflib.account.utils import is_staff
from ocflib.lab.hours import Day
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/home/s/st/staff/staff_hours_example_vaibhav.yaml'
STAFF_HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/staff_hours.yaml'
StaffDay = namedtuple('Staffday', ['day', 'hours', 'holiday'])
Hour = namedtuple('Hour', ['day', 'time', 'staff', 'cancelled'])

string_to_constant = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
                      'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}

seconds_in_day = 24 * 3600
seconds_in_half_a_day = 12 * 3600
seconds_in_a_hour = 3600
seconds_in_a_min = 60
days_in_week = 7


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


def convert_to_sec_from_day_start(digital_time_string):
    secs = 0
    colon_index = digital_time_string.find(':')
    if (colon_index != -1):
        secs += int((digital_time_string[colon_index + 1:]).strip()) \
            * seconds_in_a_min
        secs += int((digital_time_string[:colon_index]).strip()) \
            * seconds_in_a_hour
    else:
        secs += int((digital_time_string).strip()) * seconds_in_a_hour
    return secs


def parse_time_string_with_am_pm(time, end=True):
    num_of_secs = 0
    am_or_pm = None
    time_string_end = None
    if (time_string_end):
        time_string_end = time[time.index('-') + 1:]
    else:
        time_string_end = time[:time.index('-')]
    time_string_end = time_string_end.strip()
    am_or_pm = time_string_end[-2]
    if (am_or_pm == 'p'):
        num_of_secs = seconds_in_half_a_day
    num_of_secs += convert_to_sec_from_day_start(time_string_end[:-2])
    return num_of_secs


def date_is_holiday(name_of_day):
    # come up with a better way to convert from the day given in the textfile
    today = date.today()
    modded_day = today.isoweekday() % string_to_constant['Sunday']
    date_object = Day.from_date(today + timedelta(days=string_to_constant[name_of_day] - modded_day))
    return date_object.holiday


def get_staff_hours():
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
    return sorted(lst_of_staff_days, key=lambda staff_day:
                  string_to_constant[staff_day.day])


def get_staff_hours_per_day(day, staff_hours, name_of_day):

    def position(uid):
        if uid in staff_hours['staff-positions']:
            return staff_hours['staff-positions'][uid]
        elif is_staff(uid, group='ocfroot'):
            return 'Technical Manager'
        else:
            return 'Staff Member'

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
             ) for hour in day], key=lambda hour:
        parse_time_string_with_am_pm(hour.time, False))


def _remove_middle_names(name):
    names = name.split(' ')
    return names[0] + ' ' + names[-1]


def get_staff_hours_soonest_first():
    today = date.today()

    def determine_hours_away(hour):
        now = 0
        hours_away_in_sec = 0
        time_as_string = hour.time
        day = hour.day
        day_diff = string_to_constant[day] - today.isoweekday()
        now = dtime.now().strftime('%H:%M')

        def parse_time_string_no_am_pm(time):
            return convert_to_sec_from_day_start(time)

        staff_hours_seconds = parse_time_string_with_am_pm(time_as_string)
        today_time_in_sec = parse_time_string_no_am_pm(now)
        earlier_in_day_or_earlier_in_week = day_diff < 0 \
            or today.isoweekday() == string_to_constant[day] \
            and staff_hours_seconds < today_time_in_sec
        if (earlier_in_day_or_earlier_in_week):
            day_diff += days_in_week

        hours_away_in_sec += day_diff * seconds_in_day
        hours_away_in_sec += staff_hours_seconds - today_time_in_sec
        return hours_away_in_sec

    hours = chain.from_iterable([staff_day.hours for staff_day in get_staff_hours()])
    hours = sorted(hours, key=lambda x: determine_hours_away(x))
    hours = [hour for hour in hours if not hour.cancelled]
    hours_with_no_cancelled_hours = [hour for hour in hours if not date_is_holiday(hour.day)]
    return(hours_with_no_cancelled_hours)
