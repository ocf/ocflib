from collections import namedtuple
from datetime import date
from datetime import timedelta
from hashlib import md5
from urllib.parse import urlencode
from itertools import chain

import requests
import yaml

from ocflib.account.search import user_attrs
from ocflib.account.utils import is_staff
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/home/s/st/staff/staff_hours_example_vaibhav.yaml'
STAFF_HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/staff_hours.yaml'

Staffday = namedtuple('Staffday', ['day','hours','no_staff_hours_today']) 
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

    def check_hours_cancelled(lst_of_hours):
        for hour in lst_of_hours:
            if (getattr(hour,'cancelled') == False):
                return False
        return True

    hour_info = staff_hours['staff-hours']
    for staff_day in hour_info:
        hours_for_day = get_staff_hours_per_day(hour_info[staff_day],staff_hours, staff_day)
        all_hours_cancelled = check_hours_cancelled(hours_for_day)
        lst_of_staff_days.append(Staffday(day = staff_day, hours = hours_for_day, 
                no_staff_hours_today = all_hours_cancelled))
    print (lst_of_staff_days)
    return lst_of_staff_days

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
    days = [(today + timedelta(days=i)).strftime('%A') for i in range(7)]
    #change to include the next two staff hours not the first two in a day
    sorted_days = sorted(get_staff_hours(), key=lambda hour: days.index(hour.day))
    hours = list(chain.from_iterable([day.hours for day in sorted_days]))
    return(hours)
