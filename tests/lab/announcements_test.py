import pytest

from ocflib.lab.announcements import get_announcement

TEST_FOLDER = 'tests'


def test_health_check():
    assert True


@pytest.mark.parametrize(
    'content, id',
    [
        ('this is a 1st test announcements', '2002-01-00-00'),
        ('this is a 2nd test announcements', '2002-01-01-00'),
        ('this is a 3rd test announcements', '2002-01-02-00'),
    ],
)
def test_get_announcement_pass(content, id):
    assert content in get_announcement(id, folder=TEST_FOLDER).text


def test_get_announcement_bad_id():
    with pytest.raises(ValueError):
        get_announcement('2002-01-01-102p', folder=TEST_FOLDER)


# @pytest.mark.parametrize
# def test_get_id_pass():
#     assert "2002-01-00-00" == get_id(
#         get_announcement("2002-01-01-10", folder=TEST_FOLDER)
#     )
