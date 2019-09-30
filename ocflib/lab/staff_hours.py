from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import timedelta
from hashlib import md5
from urllib.parse import urlencode

import yaml

from ocflib.account.search import user_attrs
from ocflib.account.utils import is_in_group
from ocflib.misc.mail import email_for_user


STAFF_HOURS_FILE = '/etc/ocf/staff_hours.yaml'

Hour = namedtuple('Hour', ['day', 'time', 'staff', 'cancelled'])


class Staffer(namedtuple('Staffer', ['user_name', 'real_name', 'position'])):

    def gravatar(self, size=100):
        email = email_for_user(self.user_name, check_exists=False)
        return 'https://www.gravatar.com/avatar/{hash}?{params}'.format(
            hash=md5(email.lower().encode('utf-8')).hexdigest(),
            params=urlencode({'d': 'mm', 's': size}),
        )


def _load_staff_hours():
    """Load staff hours, from the /etc/ocf folder."""
    with open(STAFF_HOURS_FILE, 'r') as f:
        return yaml.safe_load(f)


def get_staff_hours():
    staff_hours = _load_staff_hours()

    def position(uid):
        staff_position_dict = {entry['username']: entry['position'] for entry in staff_hours['staff-positions']}
        if uid in staff_position_dict:
            return staff_position_dict[uid]
        elif is_in_group(uid, 'ocfroot'):
            return 'Technical Manager'
        else:
            return 'Staff Member'

    staff_hour_list = []
    # If we try iterating through the keys in staff-hours, it's non-deterministic ordering.
    # Because of the schema, we are guaranteed that these days are always here.
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        if not staff_hours['staff-hours'][day]:
            continue

        for staff_hour in staff_hours['staff-hours'][day]:
            staff_hour_list.append(
                Hour(
                    day=day,
                    time=_parse_hour(staff_hour['time']),
                    staff=[
                        Staffer(
                            user_name=attrs['uid'][0],
                            real_name=_remove_middle_names(attrs['cn'][0]),
                            position=position(attrs['uid'][0]),
                        ) for attrs in map(user_attrs, staff_hour['staff'])
                    ],
                    cancelled=staff_hour.get('cancelled', False)
                )
            )

    return staff_hour_list


def _parse_hour(hour):
    """
    Converts a 2-element list of hours like ['11:00', '13:00'] to a string
    in 12-hour time, like '11:00AM - 1:00PM'.
    Needed for backwards compatibility with the old staff hours file.
    """
    return '{} - {}'.format(datetime.strptime(hour[0], '%H:%M').strftime('%-I:%M%p'),
                            datetime.strptime(hour[1], '%H:%M').strftime('%-I:%M%p'))


def _remove_middle_names(name):
    names = name.split(' ')
    return names[0] + ' ' + names[-1]


def get_staff_hours_soonest_first():
    today = date.today()
    days = [(today + timedelta(days=i)).strftime('%A') for i in range(7)]
    return sorted(get_staff_hours(), key=lambda hour: days.index(hour.day))
