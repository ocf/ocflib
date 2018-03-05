from datetime import datetime

import mock
import pytest
import yaml

from ocflib.lab.staff_hours import _load_staff_hours
from ocflib.lab.staff_hours import date_is_holiday
from ocflib.lab.staff_hours import get_staff_hours
from ocflib.lab.staff_hours import get_staff_hours_soonest_first
from ocflib.lab.staff_hours import Hour
from ocflib.lab.staff_hours import StaffDay
from ocflib.lab.staff_hours import Staffer


TEST_HOURS = """\
    staff-hours:
      Monday:
        4:10pm-5:00pm:
          staff: [nickimp, ckuehl, lynntsai]
          cancelled: false
      Tuesday:
        3:10pm-4:00pm:
          staff: [willh]
          cancelled: true
        4:10pm-5:00pm:
          staff: [willh]
          cancelled: false

    staff-positions:
        ckuehl: Site Manager
        willh: Deputy Manager
        nickimp: General Manager
"""


@pytest.yield_fixture
def mock_disk(tmpdir):
    f = tmpdir.join('staff_hours.yaml')
    f.write(TEST_HOURS)
    with mock.patch('ocflib.lab.staff_hours.STAFF_HOURS_FILE', f.strpath):
        yield


@pytest.yield_fixture
def mock_web():
    with mock.patch('requests.get') as m:
        yield m


@pytest.yield_fixture
def mock_not_on_disk(tmpdir):
    with mock.patch(
        'ocflib.lab.staff_hours.STAFF_HOURS_FILE',
        tmpdir.join('does-not-exist').strpath
    ):
        yield


@pytest.yield_fixture
def mock_on_web(mock_web):
    mock_web.return_value.text = TEST_HOURS
    yield


class TestLoadStaffHours:

    def test_loads_from_file_if_exists(self, mock_web, mock_disk):
        assert _load_staff_hours() == yaml.safe_load(TEST_HOURS)
        assert not mock_web.called

    def test_loads_from_web_otherwise(self, mock_not_on_disk, mock_web, mock_on_web):
        assert _load_staff_hours() == yaml.safe_load(TEST_HOURS)
        assert mock_web.called


def test_get_staff_hours(mock_disk):
    assert get_staff_hours() == [
        StaffDay(day='Monday',
                 hours=[
                     Hour(
                         day='Monday',
                         time='4:10pm-5:00pm',
                         staff=[
                             Staffer(
                                 user_name='nickimp',
                                 real_name='Nick Impicciche',
                                 position='General Manager',
                             ),
                             Staffer(
                                 user_name='ckuehl',
                                 real_name='Chris Kuehl',
                                 position='Site Manager',
                             ),
                             Staffer(
                                 user_name='lynntsai',
                                 real_name='Lynn Tsai',
                                 position='Staff Member',
                             ),
                         ],
                         cancelled=False,
                     )],
                 holiday=date_is_holiday('Monday')),
        StaffDay(day='Tuesday',
                 hours=[
                     Hour(
                         day='Tuesday',
                         time='3:10pm-4:00pm',
                         staff=[
                             Staffer(
                                 user_name='willh',
                                 real_name='William Ho',
                                 position='Deputy Manager',
                             )
                         ],
                         cancelled=True),
                     Hour(
                         day='Tuesday',
                         time='4:10pm-5:00pm',
                         staff=[Staffer(
                             user_name='willh',
                             real_name='William Ho',
                             position='Deputy Manager')],
                         cancelled=False)],
                 holiday=date_is_holiday('Tuesday'))
    ]


@pytest.mark.parametrize('time,expected', [
    ('2015-08-23 9:33 am', ['Monday', 'Tuesday']),  # Sunday
    ('2015-08-24 9:33 am', ['Monday', 'Tuesday']),  # Monday Morning
    ('2015-08-24 5:01 pm', ['Tuesday', 'Monday']),  # Monday evening
    ('2015-08-25 9:33 am', ['Tuesday', 'Monday']),  # Tueday Morning
    ('2015-08-25 3:33 pm', ['Tuesday', 'Monday']),  # Tuesday during cancelled hours
    ('2015-08-25 4:15 pm', ['Tuesday', 'Monday']),  # Tuesday during staff hours
    ('2015-08-27 9:33 am', ['Monday', 'Tuesday']),  # Thursday morning
    ('2015-08-29 1:00 pm', ['Monday', 'Tuesday']),  # Saturday Afternoon
])
def test_get_staff_hours_soonest_first(mock_disk, time, expected):
    test_time = datetime.strptime(time, '%Y-%m-%d %I:%M %p')
    print(test_time)
    assert [hour.day for hour in get_staff_hours_soonest_first(test_time)] == expected


@pytest.mark.parametrize('size', [10, 100, 1000])
def test_gravatars(size):
    staffer = Staffer(
        user_name='ckuehl',
        real_name='Chris Kuehl',
        position='Site Manager',
    )
    url = staffer.gravatar(size)
    assert url.startswith('https://www.gravatar.com/avatar/b4a3363de72988194e4b9c25195c3d07?')
    assert ('s=' + str(size)) in url.split('?')[1].split('&')
