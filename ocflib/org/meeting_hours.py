"""Methods for tracking meeting times across OCF.

All times are assumed to be OST (OCF Standard Time).
"""

from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import timedelta

import time
import yaml

MEETING_HOURS_FILE = '/etc/ocf/meeting_hours.yaml'

Meeting = namedtuple('Meeting', ['day', 'time', 'subject', 'short', 'irl', 'virtual'])

def _load_meeting_hours():
    """Load meeting hours, from the /etc/ocf folder."""
    with open(MEETING_HOURS_FILE, 'r') as f:
        return yaml.safe_load(f)

def _get_meeting_hours():
    meeting_hours = _load_meeting_hours()

    meeting_hour_list = []

    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        if not meeting_hours['meeting_hours'][day]:
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
    return '{} - {}'.format(datetime.strptime(hour[0], '%H:%M').strftime('%-I:%M%p'),
                            datetime.strptime(hour[1], '%H:%M').strftime('%-I:%M%p'))

