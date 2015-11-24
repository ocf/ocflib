from collections import namedtuple
from datetime import timedelta

import pymysql
from cached_property import cached_property

from ocflib.constants import OCF_LDAP_HOSTS
from ocflib.infra.ldap import ldap_ocf


def get_connection(user='anonymous', password=None):
    return pymysql.connect(
        host='mysql.ocf.berkeley.edu',
        user=user,
        password=password,
        db='ocfstats',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


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
                    ORDER BY `start` ASC
            """

            c.execute(query, (hostname, start, end, start, end, start, end, start))

            return cls(
                hostname=hostname,
                start=start,
                end=end,
                sessions=[(r['start'], r['end']) for r in c],
            )

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
