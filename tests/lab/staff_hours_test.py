import mock
import pytest
import yaml
from freezegun import freeze_time

from ocflib.lab.staff_hours import _load_staff_hours
from ocflib.lab.staff_hours import get_staff_hours
from ocflib.lab.staff_hours import get_staff_hours_soonest_first
from ocflib.lab.staff_hours import Hour
from ocflib.lab.staff_hours import Staffer


TEST_HOURS = """\
staff-hours:
  Monday:
   - time: ['16:10', '17:00']
     staff: ["nickimp", "ckuehl", "lynntsai"]
  Tuesday:
   - time: ['15:10', '16:00']
     staff: ["willh"]
     cancelled: true
  Wednesday:
  Thursday:
  Friday:
  Saturday:
  Sunday:

staff-positions:
 - username: "willh"
   position: "Deputy Manager"
 - username: "nickimp"
   position: "General Manager"
"""


@pytest.yield_fixture
def mock_disk(tmpdir):
    f = tmpdir.join('staff_hours.yaml')
    f.write(TEST_HOURS)
    with mock.patch('ocflib.lab.staff_hours.STAFF_HOURS_FILE', f.strpath):
        yield


class TestLoadStaffHours:

    def test_loads_from_file_if_exists(self, mock_disk):
        assert _load_staff_hours() == yaml.safe_load(TEST_HOURS)


def test_get_staff_hours(mock_disk):
    assert get_staff_hours() == [
        Hour(
            day='Monday',
            time='4:10PM - 5:00PM',
            staff=[
                Staffer(
                    user_name='nickimp',
                    real_name='Nick Impicciche',
                    position='General Manager',
                ),
                Staffer(
                    user_name='ckuehl',
                    real_name='Chris Kuehl',
                    position='Technical Manager',
                ),
                Staffer(
                    user_name='lynntsai',
                    real_name='Lynn Tsai',
                    position='Staff Member',
                ),
            ],
            cancelled=False,
        ),
        Hour(
            day='Tuesday',
            time='3:10PM - 4:00PM',
            staff=[
                Staffer(
                    user_name='willh',
                    real_name='William Ho',
                    position='Deputy Manager',
                )
            ],
            cancelled=True,
        ),
    ]


@pytest.mark.parametrize('time,expected', [
    ('2015-08-23', ['Monday', 'Tuesday']),  # Sunday
    ('2015-08-24', ['Monday', 'Tuesday']),  # Monday
    ('2015-08-25', ['Tuesday', 'Monday']),  # Tuesday
    ('2015-08-26', ['Monday', 'Tuesday']),  # Wednesday
])
def test_get_staff_hours_soonest_first(mock_disk, time, expected):
    with freeze_time(time):
        assert [hour.day for hour in get_staff_hours_soonest_first()] == expected


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
