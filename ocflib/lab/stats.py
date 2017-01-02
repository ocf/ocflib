from collections import defaultdict
from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import timedelta

import pymysql
from cached_property import cached_property

from ocflib.constants import OCF_LDAP_HOSTS
from ocflib.infra.ldap import ldap_ocf


# when we started keeping stats
STATS_EPOCH = date(2014, 2, 15)


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


def get_connection(user='anonymous', password=None, **kwargs):
    """Return a connection to MySQL.

    By default, returns an unprivileged connection which can be used for
    querying most data.

    If you need rw access, pass a user and password argument.
    """
    return pymysql.connect(
        host='mysql.ocf.berkeley.edu',
        user=user,
        password=password,
        db='ocfstats',
        cursorclass=pymysql.cursors.DictCursor,
        **dict({'autocommit': True}, **kwargs)
    )


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


def current_semester_start():
    today = date.today()
    if today.month >= 8:
        return today.replace(month=8, day=1)
    else:
        return today.replace(month=1, day=1)


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
        filter = '(&(type=desktop)(!(|(puppetVar=staff_only=true)(puppetVar=pubstaff_only=true))))'

    with ldap_ocf() as c:
        c.search(OCF_LDAP_HOSTS, filter, attributes=['cn'])
        return [entry['attributes']['cn'][0] for entry in c.response]


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
        def add_ocf(hostname):
            if not hostname.endswith('.ocf.berkeley.edu'):
                return hostname + '.ocf.berkeley.edu'
            return hostname

        hostnames = tuple(map(add_ocf, hostnames))

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
