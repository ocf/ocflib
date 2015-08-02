import mock
import pytest

from ocflib.misc.whoami import current_uid
from ocflib.misc.whoami import current_user
from ocflib.misc.whoami import current_user_email
from ocflib.misc.whoami import current_user_formatted_email
from ocflib.misc.whoami import current_user_fullname


@pytest.yield_fixture
def mock_uid():
    UID = 28460
    with mock.patch('os.getuid', return_value=UID):
        yield UID


@pytest.yield_fixture
def mock_getpwuid():
    passwd = mock.Mock(
        pw_name='ckuehl',
        pw_passwd='hunter2',
        pw_uid=28460,
        pw_gid=1000,
        pw_gecos='Chris Kuehl',
        pw_dir='/home/c/ck/ckuehl',
        pw_shell='/bin/zsh',
    )
    with mock.patch('pwd.getpwuid', return_value=passwd):
        yield passwd


def test_current_uid(mock_uid):
    assert current_uid() == mock_uid


def test_current_user(mock_uid, mock_getpwuid):
    assert current_user() == mock_getpwuid.pw_name


def test_current_user_fullname(mock_uid, mock_getpwuid):
    assert current_user_fullname() == mock_getpwuid.pw_gecos


def test_current_user_email(mock_uid, mock_getpwuid):
    assert current_user_email() == '{username}@ocf.berkeley.edu'.format(
        username=mock_getpwuid.pw_name,
    )


def test_current_user_formatted_email(mock_uid, mock_getpwuid):
    expected = '{name} <{username}@ocf.berkeley.edu>'.format(
        name=mock_getpwuid.pw_gecos,
        username=mock_getpwuid.pw_name,
    )
    assert current_user_formatted_email() == expected
