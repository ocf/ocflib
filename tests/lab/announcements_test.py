import pytest
from requests.exceptions import HTTPError

from ocflib.lab.announcements import get_all_announcements
from ocflib.lab.announcements import get_announcement
from ocflib.lab.announcements import get_id

TEST_FOLDER = 'tests'
TEST_IDS = [
    '2002-01-01-00',
    '2002-01-01-01',
    '2002-01-02-00',
    '2023-09-01-00',
    '2023-10-01-00',
    '2023-11-01-00',
]


# scope = module means that the fixture is only run once per module
@pytest.fixture(scope='module')
def test_annoucement_health_check() -> [dict]:
    return get_all_announcements(folder=TEST_FOLDER)


@pytest.mark.parametrize(
    'id',
    TEST_IDS,
)
def test_get_announcement_pass(id):
    assert 'testing' in get_announcement(id, folder=TEST_FOLDER)


@pytest.mark.parametrize(
    'id',
    [
        '2002-01-00-00212',
        '2002-01-01-aa',
        '2002-01-02-21a',
        '202-01-02-00',
        '2002-223-02-00',
        '2002-01-80-00',
    ],
)
def test_get_announcement_bad_id(id):
    with pytest.raises(ValueError):
        get_announcement(id, folder=TEST_FOLDER)


# Those announcements don't exist in the test folder
@pytest.mark.parametrize(
    'id',
    [
        '2002-01-01-10',
        '2002-01-01-12',
        '2002-01-02-30',
    ],
)
def test_get_announcement_fail(id):
    with pytest.raises(HTTPError):
        get_announcement(id, folder=TEST_FOLDER)


@pytest.mark.parametrize('id', TEST_IDS)
def test_get_id_pass(id, test_annoucement_health_check):
    found = False
    for post in test_annoucement_health_check:
        if id == get_id(post):
            found = True
            break
    assert found, f'ID {id} not found in announcements'


@pytest.mark.parametrize(
    'id',
    [
        '2002-01-01-10',
        '2002-01-01-12',
        '2002-01-02-30',
    ],
)
def test_get_id_fail(id, test_annoucement_health_check):
    for post in test_annoucement_health_check:
        assert id != get_id(post), f'Unexpected ID {id} found in announcements'


# @pytest.mark.parametrize()
# def test_get_metadata_pass(content):
#     pass


# @pytest.mark.parametrize()
# def test_get_metadata_bad_format(content):
#     pass


# @pytest.mark.parametrize()
# def test_get_metadata_missing_metadata(content):
#     pass


# @pytest.mark.parametrize()
# def test_get_last_n_announcements_text_pass(content):
#     pass


# @pytest.mark.parametrize()
# def test_get_last_n_announcements_text_bad_n(content):
#     pass
