from datetime import datetime
from datetime import timedelta

import mock
import pkg_resources
import pytest
from freezegun import freeze_time

from ocflib.printing.quota import add_job
from ocflib.printing.quota import add_refund
from ocflib.printing.quota import daily_quota
from ocflib.printing.quota import get_quota
from ocflib.printing.quota import Job
from ocflib.printing.quota import Refund
from ocflib.printing.quota import SEMESTERLY_QUOTA
from ocflib.printing.quota import UserQuota
from ocflib.printing.quota import WEEKDAY_QUOTA
from ocflib.printing.quota import WEEKEND_QUOTA


FAKE_DAILY_QUOTA = 1000
FAKE_SEMESTERLY_QUOTA = 10000

TODAY = datetime.today()
YESTERDAY = TODAY - timedelta(days=1)
LAST_SEMESTER = TODAY - timedelta(days=365)

TEST_JOB = Job(
    user='mattmcal',
    time=datetime.now(),
    pages=3,
    queue='double',
    printer='logjam',
    doc_name='asdf',
    filesize=12,
)
TEST_REFUND = Refund(
    user='mattmcal',
    time=datetime.now(),
    pages=3,
    staffer='ckuehl',
    reason='just because',
)


@pytest.mark.parametrize('time,expected', [
    ('2015-08-22', WEEKEND_QUOTA),  # Saturday
    ('2015-08-23', WEEKEND_QUOTA),  # Sunday
    ('2015-08-24', WEEKDAY_QUOTA),  # Monday
    ('2015-08-25', WEEKDAY_QUOTA),  # Tuesday
    ('2015-08-26', WEEKDAY_QUOTA),  # Wednesday
])
def test_daily_quota(time, expected):
    """Test that the daily quota returns reasonable things."""
    time = datetime.strptime(time, '%Y-%m-%d')
    with freeze_time(time):
        assert daily_quota() == expected
    assert daily_quota(time) == expected


def test_quotas_are_sane():
    assert SEMESTERLY_QUOTA > 0
    assert WEEKDAY_QUOTA > 0
    assert WEEKEND_QUOTA > WEEKDAY_QUOTA
    assert WEEKDAY_QUOTA < SEMESTERLY_QUOTA
    assert WEEKEND_QUOTA < SEMESTERLY_QUOTA


def assert_quota(c, user, diff_daily, diff_semesterly):
    """Assert the quota for a user is what we expect.

    Typically, you want to pass a negative number for diff_daily and
    diff_semesterly. This number is added to the start quota before assertion.
    """
    start = 1000, 10000
    with mock.patch('ocflib.printing.quota.daily_quota', return_value=start[0]), \
            mock.patch('ocflib.printing.quota.SEMESTERLY_QUOTA', start[1]):
        assert (
            get_quota(c, user) ==
            UserQuota(user, FAKE_DAILY_QUOTA + diff_daily, FAKE_SEMESTERLY_QUOTA + diff_semesterly)
        )


@pytest.mark.parametrize('user', ('mattmcal', 'ckuehl'))
def test_quota_user_not_in_db(user, mysql_connection):
    assert_quota(mysql_connection, user, 0, 0)


def test_pubstaff_has_infinite_quota(mysql_connection):
    assert (
        get_quota(mysql_connection, 'pubstaff') ==
        UserQuota('pubstaff', 500, 500)
    )


def test_groups_have_zero_quota(mysql_connection):
    assert (
        get_quota(mysql_connection, 'ggroup') ==
        UserQuota('ggroup', 0, 0)
    )


def test_non_existent_users_have_zero_quota(mysql_connection):
    assert (
        get_quota(mysql_connection, 'nonexist') ==
        UserQuota('nonexist', 0, 0)
    )


@pytest.mark.parametrize('doc_name', [
    'éóñəå  ⊂(◉‿◉)つ(ノ≥∇≤)ノ',
    '¯\_(ツ)_/¯',
    '♪┏(・o･)┛♪┗ ( ･o･) ┓♪┏ ( ) ┛♪┗ (･o･ ) ┓♪┏(･o･)┛♪',
    'éóñå',
    '😺 😸 😻 😽 😼 🙀 😿 😹 😾',
])
def test_job_with_weird_chars_works(doc_name, mysql_connection):
    """Jobs with non-ASCII characters should still be added."""
    assert_quota(mysql_connection, 'mattmcal', 0, 0)

    add_job(mysql_connection, TEST_JOB._replace(pages=5, doc_name=doc_name))
    assert_quota(mysql_connection, 'mattmcal', -5, -5)


def test_semesterly_quota_limits_daily_quota(mysql_connection):
    """The daily quota should be limited by the semesterly quota."""
    assert_quota(mysql_connection, 'mattmcal', 0, 0)

    add_job(mysql_connection, TEST_JOB._replace(pages=FAKE_SEMESTERLY_QUOTA - 5, time=YESTERDAY))
    assert_quota(mysql_connection, 'mattmcal', -FAKE_DAILY_QUOTA + 5, -FAKE_SEMESTERLY_QUOTA + 5)

    add_job(mysql_connection, TEST_JOB._replace(pages=5, time=YESTERDAY))
    assert_quota(mysql_connection, 'mattmcal', -FAKE_DAILY_QUOTA, -FAKE_SEMESTERLY_QUOTA)

    # and now we should hit a floor at zero even if we somehow exceeded the quota
    add_job(mysql_connection, TEST_JOB._replace(pages=3, time=YESTERDAY))
    assert_quota(mysql_connection, 'mattmcal', -FAKE_DAILY_QUOTA, -FAKE_SEMESTERLY_QUOTA)


def test_several_jobs_today(mysql_connection):
    """Multiple jobs should decrease quota correctly."""
    assert_quota(mysql_connection, 'mattmcal', 0, 0)

    add_job(mysql_connection, TEST_JOB._replace(pages=3))
    assert_quota(mysql_connection, 'mattmcal', -3, -3)

    add_job(mysql_connection, TEST_JOB._replace(pages=8))
    assert_quota(mysql_connection, 'mattmcal', -11, -11)

    # now add another user
    assert_quota(mysql_connection, 'ckuehl', 0, 0)

    add_job(mysql_connection, TEST_JOB._replace(pages=5, user='ckuehl'))
    assert_quota(mysql_connection, 'ckuehl', -5, -5)
    assert_quota(mysql_connection, 'mattmcal', -11, -11)


def test_several_jobs_previous_days_and_semesters(mysql_connection):
    """Multiple jobs should decrease quota correctly over different days,
    semesters, and users."""
    for user in ('mattmcal', 'ckuehl', 'jvperrin'):
        assert_quota(mysql_connection, user, 0, 0)

        # add some jobs today
        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=1, time=TODAY))
        assert_quota(mysql_connection, user, -1, -1)

        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=2, time=TODAY))
        assert_quota(mysql_connection, user, -3, -3)

        # add some jobs yesterday
        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=3, time=YESTERDAY))
        assert_quota(mysql_connection, user, -3, -6)

        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=5, time=YESTERDAY))
        assert_quota(mysql_connection, user, -3, -11)

        # add some jobs last semester
        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=8, time=LAST_SEMESTER))
        assert_quota(mysql_connection, user, -3, -11)

        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=13, time=LAST_SEMESTER))
        assert_quota(mysql_connection, user, -3, -11)


def test_get_quota_user_not_printed_today(mysql_connection):
    """If a user hasn't printed today, we should still be able to get their
    quota."""
    # a user who printed only yesterday
    add_job(mysql_connection, TEST_JOB._replace(user='mattmcal', pages=13, time=YESTERDAY))
    assert_quota(mysql_connection, 'mattmcal', 0, -13)

    # a user who printed only last semester
    add_job(mysql_connection, TEST_JOB._replace(user='ckuehl', pages=13, time=LAST_SEMESTER))
    assert_quota(mysql_connection, 'ckuehl', 0, 0)


def test_refunds_without_jobs(mysql_connection):
    """We should be able to calculate quotas correctly for a user with a refund
    but no jobs."""
    # a user with no jobs at all but a refund today
    assert_quota(mysql_connection, 'ckuehl', 0, 0)

    add_refund(mysql_connection, TEST_REFUND._replace(user='ckuehl', pages=10))
    assert_quota(mysql_connection, 'ckuehl', 10, 10)

    # a user with no jobs today and a refund earlier in the semester
    add_job(mysql_connection, TEST_JOB._replace(user='mattmcal', pages=5, time=YESTERDAY))
    assert_quota(mysql_connection, 'mattmcal', 0, -5)

    add_refund(mysql_connection, TEST_REFUND._replace(user='mattmcal', pages=10, time=YESTERDAY))
    assert_quota(mysql_connection, 'mattmcal', 0, 5)

    # a user with no jobs today and a refund today
    add_job(mysql_connection, TEST_JOB._replace(user='jvperrin', pages=5, time=YESTERDAY))
    assert_quota(mysql_connection, 'jvperrin', 0, -5)

    add_refund(mysql_connection, TEST_REFUND._replace(user='jvperrin', pages=10))
    assert_quota(mysql_connection, 'jvperrin', 10, 5)

    # a user with just one job (today) but a refund earlier in the semester
    add_job(mysql_connection, TEST_JOB._replace(user='kpengboy', pages=5))
    assert_quota(mysql_connection, 'kpengboy', -5, -5)

    add_refund(mysql_connection, TEST_REFUND._replace(user='kpengboy', pages=10, time=YESTERDAY))
    assert_quota(mysql_connection, 'kpengboy', -5, 5)


def test_jobs_and_refunds_today(mysql_connection):
    """Refunds should add back pages correctly."""
    assert_quota(mysql_connection, 'mattmcal', 0, 0)

    add_job(mysql_connection, TEST_JOB._replace(pages=3))
    assert_quota(mysql_connection, 'mattmcal', -3, -3)

    add_job(mysql_connection, TEST_JOB._replace(pages=5))
    assert_quota(mysql_connection, 'mattmcal', -8, -8)

    add_refund(mysql_connection, TEST_REFUND._replace(pages=1))
    assert_quota(mysql_connection, 'mattmcal', -7, -7)

    add_refund(mysql_connection, TEST_REFUND._replace(pages=3))
    assert_quota(mysql_connection, 'mattmcal', -4, -4)

    # now add another user
    assert_quota(mysql_connection, 'ckuehl', 0, 0)

    add_job(mysql_connection, TEST_JOB._replace(pages=5, user='ckuehl'))
    assert_quota(mysql_connection, 'ckuehl', -5, -5)
    assert_quota(mysql_connection, 'mattmcal', -4, -4)

    # and some refunds for that user
    add_refund(mysql_connection, TEST_REFUND._replace(pages=8, user='ckuehl'))
    assert_quota(mysql_connection, 'ckuehl', 3, 3)
    assert_quota(mysql_connection, 'mattmcal', -4, -4)

    add_refund(mysql_connection, TEST_REFUND._replace(pages=30, user='ckuehl'))
    assert_quota(mysql_connection, 'ckuehl', 33, 33)
    assert_quota(mysql_connection, 'mattmcal', -4, -4)


def test_several_jobs_refunds_previous_days_and_semesters(mysql_connection):
    """Multiple jobs and refunds should change the quota correctly over
    different days, semesters, and users."""

    for user in ('mattmcal', 'ckuehl', 'jvperrin'):
        assert_quota(mysql_connection, user, 0, 0)

        # add some jobs and refunds today
        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=1, time=TODAY))
        assert_quota(mysql_connection, user, -1, -1)

        add_refund(mysql_connection, TEST_REFUND._replace(user=user, pages=30))
        assert_quota(mysql_connection, user, 29, 29)

        add_job(mysql_connection, TEST_JOB._replace(user=user, pages=15, time=TODAY))
        assert_quota(mysql_connection, user, 14, 14)

        add_refund(mysql_connection, TEST_REFUND._replace(user=user, pages=3))
        assert_quota(mysql_connection, user, 17, 17)

        # add some refunds yesterday
        add_refund(mysql_connection, TEST_REFUND._replace(user=user, pages=3, time=YESTERDAY))
        assert_quota(mysql_connection, user, 17, 20)

        add_refund(mysql_connection, TEST_REFUND._replace(user=user, pages=8, time=YESTERDAY))
        assert_quota(mysql_connection, user, 17, 28)

        # add some refunds last semester
        add_refund(mysql_connection, TEST_REFUND._replace(user=user, pages=8, time=LAST_SEMESTER))
        assert_quota(mysql_connection, user, 17, 28)

        add_refund(mysql_connection, TEST_REFUND._replace(user=user, pages=3, time=LAST_SEMESTER))
        assert_quota(mysql_connection, user, 17, 28)


@pytest.yield_fixture
def mysql_connection(mysql_database):
    schema = pkg_resources.resource_string('ocflib.printing', 'ocfprinting.sql')
    schema = schema.replace(  # pretty hacky...
        b'GRANT SELECT ON `ocfprinting`.',
        b'GRANT SELECT ON `' + mysql_database.db_name.encode('ascii') + b'`.',
    )
    mysql_database.run_cli_query(schema)

    with mysql_database.connection() as c:
        yield c
