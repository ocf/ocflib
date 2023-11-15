import pytest
from requests.exceptions import HTTPError

from ocflib.lab.announcements import get_all_announcements
from ocflib.lab.announcements import get_announcement
from ocflib.lab.announcements import get_id
from ocflib.lab.announcements import get_metadata

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
def get_all() -> [dict]:
    return get_all_announcements(folder=TEST_FOLDER)


# scope = module means that the fixture is only run once per module
@pytest.fixture(scope='module')
def announcement_data():
    # Fetch data once for all tests in this module
    return {id: get_announcement(id, folder=TEST_FOLDER) for id in TEST_IDS}


# Health check
@pytest.mark.parametrize(
    'id',
    TEST_IDS,
)
def test_get_announcement_pass(id):
    assert 'testing' in get_announcement(id, folder=TEST_FOLDER)


# Those ids are invalid
@pytest.mark.parametrize(
    'id',
    [
        '2002-01-00-00212',
        '2002-01-01-aa',
        '2002-01-02-21a',
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


# Those ids are valid
@pytest.mark.parametrize('id', TEST_IDS)
def test_get_id_pass(id, get_all):
    found = False
    for post in get_all:
        if id == get_id(post):
            found = True
            break
    assert found, f'ID {id} not found in announcements'


# Those ids don't exist in the test folder
@pytest.mark.parametrize(
    'id',
    [
        '2002-01-01-10',
        '2002-01-01-12',
        '2002-01-02-30',
    ],
)
def test_get_id_fail(id, get_all):
    for post in get_all:
        assert id != get_id(post), f'Unexpected ID {id} found in announcements'


@pytest.mark.parametrize('id', TEST_IDS)
def test_get_metadata_pass(id, announcement_data):
    content = announcement_data[id]
    assert 'Victor' == get_metadata(content).author, 'author not found in metadata'


def test_get_metadata_missing_metadata():
    content = """
    ---
    title: test
    date: 2020-01-01
    ---
    """
    with pytest.raises(KeyError):
        get_metadata(content)


def test_get_metadata_bad_format():
    content = """
    title: test
    date: 2020-01-01
    """
    with pytest.raises(IndexError):
        get_metadata(content)


# @pytest.mark.parametrize()
# def test_get_last_n_announcements_text_pass(content):
#     pass


# @pytest.mark.parametrize()
# def test_get_last_n_announcements_text_bad_n(content):
#     pass
