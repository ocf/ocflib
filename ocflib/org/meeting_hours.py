"""Methods for tracking meeting times across OCF.

All times are assumed to be OST (OCF Standard Time).
"""
from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import timedelta
from time import localtime

from yaml import safe_load

MEETING_HOURS_FILE = '/etc/ocf/meeting_hours.yaml'
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday',
                'Thursday', 'Friday', 'Saturday', 'Sunday']

Meeting = namedtuple(
    'Meeting',
    ['day', 'time', 'subject', 'short', 'irl', 'virtual']
)


def _load_meeting_hours():
    """Load meeting hours, from the /etc/ocf folder."""
    with open(MEETING_HOURS_FILE, 'r') as f:
        return safe_load(f)


def _get_meeting_hours():
    meeting_hours = _load_meeting_hours()

    meeting_hour_list = []
    for day in DAYS_OF_WEEK:
        if not meeting_hours['meeting-hours'][day]:
            continue

        for meeting_hour in meeting_hours['meeting-hours'][day]:
            meeting_hour_list.append(
                Meeting(
                    day=day,
                    time=_parse_hour(meeting_hour['time']),
                    subject=meeting_hour['subject'],
                    short=meeting_hour['short'],
                    irl=meeting_hour['irl'],
                    virtual=meeting_hour['virtual'],
                )
            )

    return meeting_hour_list


def _parse_hour(hour):
    """
    Converts a 2-element list of hours like ['11:00', '13:00'] to a string
    in 12-hour time, like '11:00AM - 1:00PM'.
    """
    return '{} - {}'.format(
        datetime.strptime(
            hour[0],
            '%H:%M'
        ).strftime('%-I:%M%p'),
        datetime.strptime(
            hour[1],
            '%H:%M'
        ).strftime('%-I:%M%p')
    )


def _time_to_range(hours):
    """
    Converts a time from format '11:00AM - 1:00PM' to (660, 780)
    """
    first_colon = hours.find(':')
    if first_colon != 1 and first_colon != 2:
        return

    first_half = hours[first_colon + 3:first_colon + 5]
    if first_half != 'AM' and first_half != 'PM':
        return

    hyphen = hours.find('-')
    if hyphen == -1:
        return

    second_colon = hours.find(':', first_colon + 1)
    if second_colon != hyphen + 3 and second_colon != hyphen + 4:
        return

    second_half = hours[second_colon + 3:second_colon + 5]
    if second_half != 'AM' and second_half != 'PM':
        return

    start_hours = int(hours[0:first_colon])
    start_minutes = int(hours[first_colon + 1:first_colon + 3])
    end_hours = int(hours[hyphen + 2:second_colon])
    end_minutes = int(hours[second_colon + 1:second_colon + 3])

    start_pm_offset = 12 if first_half == 'PM' else 0
    end_pm_offset = 12 if second_half == 'PM' else 0

    start_time = start_hours * 60 + start_pm_offset * 60 + start_minutes
    end_time = end_hours * 60 + end_pm_offset * 60 + end_minutes

    return (start_time, end_time)


def _iso_weekday_to_str(num):
    if(num == 1):
        return 'Monday'
    elif(num == 2):
        return 'Tuesday'
    elif(num == 3):
        return 'Wednesday'
    elif(num == 4):
        return 'Thursday'
    elif(num == 5):
        return 'Friday'
    elif(num == 6):
        return 'Saturday'
    elif(num == 7):
        return 'Sunday'

    return ''


def _get_next_meeting(today=date.today(), now=localtime()):
    now = now.tm_hour * 60 + localtime().tm_min
    days = [(today + timedelta(days=i)).strftime('%A') for i in range(7)]

    meetings = sorted(
        _get_meeting_hours(),
        key=lambda meeting: days.index(meeting.day)
    )

    for meeting in meetings:
        ranged_time = _time_to_range(meeting.time)
        if ranged_time[0] > now or meeting.day != _iso_weekday_to_str(today.isoweekday()):
            return meeting

    return None


def _get_current_meeting(today=date.today(), now=localtime()):
    now = now.tm_hour * 60 + localtime().tm_min
    days = [(today + timedelta(days=i)).strftime('%A') for i in range(7)]

    meetings = sorted(
        _get_meeting_hours(),
        key=lambda meeting: days.index(meeting.day)
    )

    for meeting in meetings:
        ranged_time = _time_to_range(meeting.time)
        if ranged_time[0] < now and ranged_time[1] > now and meeting.day == _iso_weekday_to_str(today.isoweekday()):
            return meeting

    return None


def read_meeting_list(**kwargs):
    return _get_meeting_hours(**kwargs)


def read_next_meeting(**kwargs):
    return _get_next_meeting(**kwargs)


def read_current_meeting(**kwargs):
    return _get_current_meeting(**kwargs)
