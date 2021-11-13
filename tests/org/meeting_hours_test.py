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


@pytest.yield_fixture
def mock_disk(tmpdir):
    f = tmpdir.join('meeting_hours.yaml')
    f.write(TEST_HOURS)
    with mock.patch('ocflib.org.meeting_hours.STAFF_HOURS_FILE', f.strpath):
        yield


class TestLoadMeetingHours:

    def test_loads_from_file_if_exists(self, mock_disk):
        assert _load_meeting_hours() == yaml.safe_load(TEST_HOURS)


def test_read_meeting_list(mock_disk):
    assert read_meeting_list() == [
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
            time='8:00PM - 9:00PM',
            subject='Staff Meeting',
            short='staff',
            irl=True,
            virtual=True
        ),
        Meeting(
            day='Friday',
            time='5:00PM - 4:00PM',
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


@pytest.mark.parametrize('date,time,expected', [
    # Sunday, October 31, 2021 8:30:00 PM GMT-7
    (date.fromisoformat("2021-10-31"), time.localtime(1633318200), None),
    # Monday, November 1, 2021 1:45:00 PM GMT-7
    (date.fromisoformat("2021-11-1"), time.localtime(1635799500), None),
    # Monday, November 1, 2021 2:00:01 PM GMT-7
    (date.fromisoformat("2021-11-1"), time.localtime(1635800401), INTERNAL_MEETING_TEST),
    # Monday, November 1, 2021 2:59:59 PM GMT-7
    (date.fromisoformat("2021-11-1"), time.localtime(1635803999), INTERNAL_MEETING_TEST),
    # Monday, November 1, 2021 3:00:01 PM GMT-7
    (date.fromisoformat("2021-11-1"), time.localtime(1635804001), None),
])
def test_read_current_meeting(mock_disk, date, time, expected):
    if(expected is None):
        assert read_current_meeting(today=date, now=time) is None
    else:
        assert read_current_meeting(today=date, now=time) == expected

