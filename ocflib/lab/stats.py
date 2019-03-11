import functools
from collections import defaultdict
from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import timedelta

from cached_property import cached_property

from ocflib.infra import mysql
from ocflib.infra.hosts import domain_from_hostname
from ocflib.infra.ldap import ldap_ocf
from ocflib.infra.ldap import OCF_LDAP_HOSTS

# =====================================
# functions for user session statistics
# =====================================

# when we started keeping session stats
SESSIONS_EPOCH = date(2014, 2, 15)

get_connection = functools.partial(mysql.get_connection,
                                   user='anonymous',
                                   password=None,
                                   db='ocfstats')


class Session(namedtuple('Session', ['user', 'host', 'start', 'end'])):

    @classmethod
    def from_row(cls, row):
        return cls(
            user=row['user'],
            host=row['host'],
            start=row['start'],
            end=row.get('end'),
        )

    @property
    def duration(self):
        return (self.end or datetime.now()) - self.start


UserTime = namedtuple('UserTime', ['user', 'time'])


def users_in_lab_count():
    """Return number of users in the lab, including staff and pubstaff."""
    with get_connection() as c:
        c.execute('SELECT * FROM `users_in_lab_count_public`')
        return int(c.fetchone()['count'])


def staff_in_lab():
    """Return list of Session objects for staff currently in the lab."""
    with get_connection() as c:
        c.execute('SELECT * FROM `staff_in_lab_public`')
        return [Session.from_row(r) for r in c]


def staff_in_lab_count():
    """Return the count of unique staff in the lab"""
    # thank based ckuehl https://github.com/ocf/ocflib/pull/47#discussion_r97914296
    return len({session.user for session in staff_in_lab()})


def current_semester_start():
    return semester_dates()[0]


# function partial constants for semesters dates
_get_spring_start = functools.partial(date, month=1, day=1)
_get_spring_end = functools.partial(date, month=7, day=31)
_get_fall_start = functools.partial(date, month=8, day=1)
_get_fall_end = functools.partial(date, month=12, day=31)


def semester_dates(day=None):
    """Return a tuple (start day, end day) for the current semester.

    Defaults to today if none is provided.
    """
    if day is None:
        day = date.today()
    fall_start = _get_fall_start(year=day.year)
    if (day.month, day.day) < (fall_start.month, fall_start.day):
        return (_get_spring_start(year=day.year),
                _get_spring_end(year=day.year))
    else:
        return (_get_fall_start(year=day.year),
                _get_fall_end(year=day.year))


def top_staff(start, end=date(3000, 1, 1)):
    """Return a list of top staff users of the lab.

    :since: date object
    :return: list of UserTime objects.
    """
    with get_connection() as c:
        query = '''
            SELECT `user`, SUM(TIME_TO_SEC(`duration`)) as `seconds` FROM `staff_session_duration_public`
            WHERE (
                (`start` BETWEEN %s AND %s OR `end` BETWEEN %s AND %s) AND
                `duration` IS NOT NULL
            )
            GROUP BY `user`
            ORDER BY `seconds` DESC
        '''
        c.execute(query, (start, end, start, end))
        return [
            UserTime(user=r['user'], time=timedelta(seconds=int(r['seconds'])))
            for r in c if r['user'] != 'pubstaff'
        ]


def top_staff_alltime():
    """Return a list of top staff users of the lab since records began.

    :return: list of UserTime objects.
    """
    return top_staff(date(1970, 1, 1))


def top_staff_semester():
    """Return a list of top staff users of the lab this semester.

    :return: list of UserTime objects.
    """
    return top_staff(current_semester_start())


def list_desktops(public_only=False):
    if not public_only:
        filter = '(type=desktop)'
    else:
        filter = '(&(type=desktop)(!(|(dnsA=frontdesk)(dnsA=staffdesk))))'

    with ldap_ocf() as c:
        c.search(OCF_LDAP_HOSTS, filter, attributes=['cn'])
        return [entry['attributes']['cn'][0] for entry in c.response]


def last_used(host, ctx):
    """Show the last used statistics for a computer."""

    query = 'SELECT * FROM `session` WHERE `host` = %s ORDER BY `start` DESC LIMIT 1'
    # we can't have another user start before current user ends so here we order by start

    ctx.execute(query, host)
    return Session.from_row(ctx.fetchone())


class UtilizationProfile(namedtuple('UtilizationProfile', [
        'hostname', 'start', 'end', 'sessions'
])):
    """Representation of computer usage over a time period."""

    @classmethod
    def from_hostname(cls, hostname, start, end):
        if not hostname.endswith('.ocf.berkeley.edu'):
            hostname += '.ocf.berkeley.edu'

        with get_connection() as c:
            query = """
                SELECT `start`, `end` FROM `session_duration_public`
                    WHERE `host` = %s AND (
                        `start` BETWEEN %s AND %s OR
                        `end` BETWEEN %s AND %s OR
                        %s BETWEEN `start` AND `end` OR
                        %s BETWEEN `start` AND `end` OR
                        `start` <= %s AND `end` IS NULL )
            """

            c.execute(query, (hostname, start, end, start, end, start, end, start))

            return cls(
                hostname=hostname,
                start=start,
                end=end,
                sessions={(r['start'], r['end']) for r in c},
            )

    @classmethod
    def from_hostnames(cls, hostnames, start, end):

        hostnames = tuple(map(domain_from_hostname, hostnames))

        with get_connection() as c:
            query = """
                SELECT `host`, `start`, `end` FROM `session_duration_public`
                    WHERE `host` IN ({}) AND (
                        `start` BETWEEN %s AND %s OR
                        `end` BETWEEN %s AND %s OR
                        %s BETWEEN `start` AND `end` OR
                        %s BETWEEN `start` AND `end` OR
                        `start` <= %s AND `end` IS NULL )
            """.format(','.join(['%s'] * len(hostnames)))

            c.execute(query, hostnames + (start, end, start, end, start, end, start))

            sessions = defaultdict(set)
            for r in c:
                sessions[r['host']].add((r['start'], r['end']))

            return {
                hostname: cls(
                    hostname=hostname,
                    start=start,
                    end=end,
                    sessions=sessions[hostname],
                )
                for hostname in hostnames
            }

    def in_use(self, when):
        return any(s[0] <= when and (not s[1] or when <= s[1]) for s in self.sessions)

    @cached_property
    def total_minutes(self):
        """The total number of minutes captured by this profile."""
        return (self.end - self.start).total_seconds() // 60

    @cached_property
    def minutes_busy(self):
        """The number of minutes the computer was busy."""
        minutes_busy = 0
        cur = self.start
        one_minute = timedelta(minutes=1)

        while cur < self.end:
            if self.in_use(cur):
                minutes_busy += 1
            cur += one_minute

        return minutes_busy

    @cached_property
    def minutes_idle(self):
        """The number of minutes the computer was idle."""
        return self.total_minutes - self.minutes_busy


# ================================
# functions for mirrors statistics
# ================================

def humanize_bytes(n):
    """Convert bytes to human-readable units

    Adapted from http://stackoverflow.com/a/1094933/1979001
    """

    for unit in ['', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if n < 1024.0:
            return '{:3.2f} {}'.format(n, unit)
        n /= 1024.0


def bandwidth_by_dist(start):
    with get_connection() as c:
        c.execute(
            'SELECT `dist`, SUM(`up` + `down`) as `bandwidth` FROM `mirrors_public` WHERE `date` > %s'
            'GROUP BY `dist` ORDER BY `bandwidth` DESC', start,
        )

    return [(i['dist'], float(i['bandwidth'])) for i in c]
