from collections import namedtuple
from datetime import date
from datetime import timedelta
from hashlib import md5
from urllib.parse import urlencode

import requests
import yaml

from ocflib.account.search import user_attrs
from ocflib.account.utils import is_staff
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/home/s/st/staff/staff_hours.yaml'
STAFF_HOURS_URL = 'https://www.ocf.berkeley.edu/~staff/staff_hours.yaml'


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
    staff_hours = _load_staff_hours()

    def position(uid):
        if uid in staff_hours['staff-positions']:
            return staff_hours['staff-positions'][uid]
        elif is_staff(uid, group='ocfroot'):
            return 'Technical Manager'
        else:
            return 'Staff Member'

    return [
        Hour(
            day=hour['day'],
            time=hour['time'],
            staff=[
                Staffer(
                    user_name=attrs['uid'][0],
                    real_name=_remove_middle_names(attrs['cn'][0]),
                    position=position(attrs['uid'][0]),
                ) for attrs in map(user_attrs, hour['staff'])
            ],
            cancelled=hour['cancelled'],
        ) for hour in staff_hours['staff-hours']
    ]


def _remove_middle_names(name):
    names = name.split(' ')
    return names[0] + ' ' + names[-1]


def get_staff_hours_soonest_first():
    today = date.today()
    days = [(today + timedelta(days=i)).strftime('%A') for i in range(7)]
    return sorted(get_staff_hours(), key=lambda hour: days.index(hour.day))
