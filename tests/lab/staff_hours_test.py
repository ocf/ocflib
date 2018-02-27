import mock
import pytest
import yaml

from ocflib.lab.staff_hours import _load_staff_hours
from ocflib.lab.staff_hours import date_is_holiday
from ocflib.lab.staff_hours import get_staff_hours
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
