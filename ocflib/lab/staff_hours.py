from collections import namedtuple
from datetime import date
from datetime import timedelta
from hashlib import md5
from urllib.parse import urlencode
from itertools import chain

import requests
import yaml

from ocflib.lab.hours import Day
from ocflib.account.search import user_attrs
from ocflib.account.utils import is_staff
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/home/s/st/staff/staff_hours_example_vaibhav.yaml'
STAFF_HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/staff_hours.yaml'

Staffday = namedtuple('Staffday', ['day','hours','no_staff_hours_today', 'holiday']) 
Hour = namedtuple('Hour', ['day', 'time', 'staff', 'cancelled'])

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

def get_staff_hours():
    lst_of_staff_days= []
    staff_hours = _load_staff_hours()
    string_to_constant = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 
            'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    def check_hours_cancelled(lst_of_hours):
        for hour in lst_of_hours:
            if (getattr(hour,'cancelled') == False):
                return False
        return True

    def date_is_holiday(name_of_day):
        #come up with a better way to convert from the day given in the textfile
        today = date.today() 
        modded_day = today.isoweekday() % string_to_constant['Sunday'] 
        date_object = Day.from_date(today + timedelta(days = 
                        string_to_constant[name_of_day] - modded_day))
        return date_object.holiday
    
    hour_info = staff_hours['staff-hours']
    for staff_day in hour_info:
        hours_for_day = get_staff_hours_per_day(hour_info[staff_day],
                        staff_hours, staff_day)
        all_hours_cancelled = check_hours_cancelled(hours_for_day)
        my_holiday = date_is_holiday(staff_day)
        lst_of_staff_days.append(Staffday(day = staff_day, 
                hours = hours_for_day, 
                no_staff_hours_today = all_hours_cancelled,
                holiday = my_holiday))
    sorted_days = sorted(lst_of_staff_days, key = lambda staff_day: 
                string_to_constant[staff_day.day])
    print("In OCFLIB")
    return sorted_days

def get_staff_hours_per_day(day, staff_hours, name_of_day):
    def position(uid):
        if uid in staff_hours['staff-positions']:
            return staff_hours['staff-positions'][uid]
        elif is_staff(uid, group='ocfroot'):
            return 'Technical Manager'
        else:
            return 'Staff Member'

    return [
        Hour(day = name_of_day, time = hour,
            staff=[
                Staffer(
                    user_name=attrs['uid'][0],
                    real_name=_remove_middle_names(attrs['cn'][0]),
                    position=position(attrs['uid'][0]),
                ) for attrs in map(user_attrs, day[hour]['staff'])
            ],
            cancelled = day[hour]['cancelled'],
        ) for hour in day ]

def _remove_middle_names(name):
    names = name.split(' ')
    return names[0] + ' ' + names[-1]


def get_staff_hours_soonest_first():
    today = date.today()
    def determine_hours_away(hour):
        now = 0
        hours_away_in_sec = 0
        seconds_in_day = 24 * 3600
        seconds_in_half_a_day = 12 * 3600
        seconds_in_an_hour = 3600
        seconds_in_a_min = 60
        days_in_week = 7
        string_to_constant = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 
            'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
   
        def convert_to_sec_from_day_start(digital_time_string):
            print(digital_time_string)
            secs = 0
            colon_index = digital_time_string.find(":")
            if (colon_index != -1):
                print(type(digital_time_string))
                secs += float((digital_time_string[colon_index + 1:]).strip())* seconds_in_a_min
            secs += float((digital_time_string[:colon_index]).strip()) * seconds_in_an_hour
            return secs

        def parse_time_string_with_am_pm(time):
            num_of_secs = 0
            am_or_pm = None 
            time_string_start = time[:time.index('-')]
            am_or_pm = time_string_start[-2]
            if (am_or_pm == 'p'):
                print(am_or_pm)
                num_of_secs = seconds_in_half_a_day
            num_of_secs +=  convert_to_sec_from_day_start(time_string_start[:-2])
            return num_of_secs
        
        def parse_time_string_no_am_pm(time):
            secs = 0
            colon_index = time.find(":")
            if (colon_index != -1):
                secs += int(time[colon_index + 1:]) * seconds_in_a_min
            secs += convert_to_sec_from_day_start(time[:colon_index]) * seconds_in_a_hour
            return secs
        
        time_as_string = hour.time
        day = hour.day
        day_diff = today.isoweekday() - string_to_constant[day]
        staff_hours_seconds = parse_time_string_with_am_pm(time_as_string)
        now = date.date.now().strftime("%H:%M")
        seconds_now = parse_time_string_no_am_pm(now)
        earlier_in_day_or_earlier_in_week = day_diff < 0 \
                or today.isoweekday() == string_to_constant[day] \
                and staff_hours_second < today_second
        if (earlier_in_day_or_earlier_in_week):
            day_diff += days_in_week

        hours_away_in_sec += day_diff * seconds_in_day 
        hours_away_in_sec += staff_hour_seconds - seconds_now
        return hours_away_in_sec
        

    hours = chain.from_iterable([staff_day.hours for staff_day in get_staff_hours()])
    print(hours)
    hours = sorted(hours, key = lambda x: determine_hours_away(x))
    return(hours)


