import time
from datetime import date

import mock
import pytest
import yaml
from ocflib.org.meeting_hours import _load_meeting_hours
from ocflib.org.meeting_hours import Meeting
from ocflib.org.meeting_hours import read_current_meeting
from ocflib.org.meeting_hours import read_meeting_list
from ocflib.org.meeting_hours import read_next_meeting

TEST_HOURS = """\
meeting-hours:
  Monday:
    - time: ['14:00', '15:00']
      subject: "Internal Meeting"
      short: "internal"
      irl: true
      virtual: false
  Tuesday:
  Wednesday:
    - time: ['20:00', '21:00']
      subject: "Staff Meeting"
      short: "staff"
      irl: true
      virtual: true
  Thursday:
  Friday:
    - time: ['17:00', '16:00']
      subject: "Web Team Meeting"
      short: "web"
      irl: true
      virtual: false
  Saturday:
    - time: ['14:00', '15:00']
      subject: "Kubernetes Interest Group Meeting"
      short: "kubernetes"
      irl: true
      virtual: false
    - time: ['15:00', '16:00']
      subject: "Linux/Infra Meeting"
      short: "linux/infra"
      irl: true
      virtual: false
  Sunday:
"""

MEETING_LIST_TEST = [
    Meeting(
        day='Monday',
        time='2:00PM - 3:00PM',
        subject='Internal Meeting',
        short='internal',
        irl=True,
        virtual=False
    ),
    Meeting(
        day='Wednesday',
        time='7:00PM - 8:00PM',
        subject='Board of Directors Meeting',
        short='bod',
        irl=True,
        virtual=True
    ),
    Meeting(
        day='Wednesday',
        time='8:00PM - 9:00PM',
        subject='Staff Meeting',
        short='staff',
        irl=True,
        virtual=True
    ),
    Meeting(
        day='Friday',
        time='5:00PM - 6:00PM',
        subject='Web Team Meeting',
        short='web',
        irl=True,
        virtual=False
    ),
    Meeting(
        day='Saturday',
        time='2:00PM - 3:00PM',
        subject='Kubernetes Interest Group Meeting',
        short='kubernetes',
        irl=True,
        virtual=False
    ),
    Meeting(
        day='Saturday',
        time='3:00PM - 4:00PM',
        subject='Linux/Infra Meeting',
        short='linux/infra',
        irl=True,
        virtual=False
    )
]

INTERNAL_MEETING_TEST = Meeting(
    day='Monday',
    time='2:00PM - 3:00PM',
    subject='Internal Meeting',
    short='internal',
    irl=True,
    virtual=False
)

STAFF_MEETING_TEST = Meeting(
    day='Wednesday',
    time='8:00PM - 9:00PM',
    subject='Staff Meeting',
    short='staff',
    irl=True,
    virtual=True
)

