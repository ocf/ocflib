from collections import namedtuple
from datetime import datetime
from textwrap import dedent

import pymysql


WEEKDAY_QUOTA = 8
WEEKEND_QUOTA = 16
SEMESTERLY_QUOTA = 100

UserQuota = namedtuple('UserQuota', (
    'user',
    'daily',
    'semesterly',
))


Job = namedtuple('Job', (
    'user',
    'time',
    'pages',
    'queue',
    'printer',
    'doc_name',
    'filesize',
))

Refund = namedtuple('Refund', (
    'user',
    'time',
    'pages',
    'staffer',
    'reason',
))


def daily_quota(day=None):
    """Return the daily quota for a given day.

    :param day: date object (defaults to today)
    """
    if day is None:
        day = datetime.today()

    if day.weekday() in {5, 6}:
        return WEEKEND_QUOTA
    else:
        return WEEKDAY_QUOTA


def get_quota(c, user):
    """Return a UserQuota representing the user's quota."""
    if user == 'pubstaff':
        return UserQuota('pubstaff', 500, 500)

    c.execute(
        'SELECT `today`, `semester` FROM `printed` WHERE `user` = %s',
        (user,)
    )

    row = c.fetchone()
    if not row:
        row = {'today': 0, 'semester': 0}
    return UserQuota(
        user=user,
        daily=daily_quota() - int(row['today']),
        semesterly=SEMESTERLY_QUOTA - int(row['semester']),
    )


def add_job(c, job):
    """Add a new job to the database."""
    c.execute(
        '''
        INSERT INTO
            `jobs`
                (`user`, `time`, `pages`, `queue`, `printer`, `doc_name`, `filesize`)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s);
        ''',
        (
            job.user,
            job.time,
            job.pages,
            job.queue,
            job.printer,
            job.doc_name,
            job.filesize,
        ),
    )


def add_refund(c, refund):
    """Add a new refund to the database."""
    c.execute(
        '''
        INSERT INTO
            `refunds`
                (`user`, `time`, `pages`, `staffer`, `reason`)
            VALUES
                (%s, %s, %s, %s, %s);
        ''',
        (
            refund.user,
            refund.time,
            refund.pages,
            refund.staffer,
            refund.reason
        ),
    )


def get_connection(user='anonymous', password=None):
    """Return a connection to MySQL.

    By default, returns an unprivileged connection which can be used for
    querying most data.

    If you need rw access, pass a user and password argument.
    """
    return pymysql.connect(
        host='mysql.ocf.berkeley.edu',
        user=user,
        password=password,
        db='ocfprinting',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def get_schema():
    """Return the printing schema.

    Normally, this never needs to be called and just exists to document the
    existing schema.
    """
    schema = dedent(
        '''\
        CREATE TABLE IF NOT EXISTS `jobs` (
            `id` int NOT NULL AUTO_INCREMENT,
            `user` varchar(255) NOT NULL,
            `time` datetime NOT NULL,
            `pages` int unsigned NOT NULL,
            `queue` varchar(255) NOT NULL,
            `printer` varchar(255) NOT NULL,
            `doc_name` varchar(510) NOT NULL,
            `filesize` int unsigned NOT NULL,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB;

        CREATE TABLE IF NOT EXISTS `refunds` (
            `id` int NOT NULL AUTO_INCREMENT,
            `user` varchar(255) NOT NULL,
            `time` datetime NOT NULL,
            `pages` int NOT NULL,
            `staffer` varchar(255) NOT NULL,
            `reason` varchar(510) NOT NULL,
            PRIMARY KEY(`id`)
        ) ENGINE=InnoDB;

        DROP INDEX jobs_idx on jobs;
        CREATE INDEX `jobs_idx` ON `jobs` (`user`, `time`, `pages`);
        DROP INDEX refunds_idx on refunds;
        CREATE INDEX `refunds_idx` ON `refunds` (`user`, `time`, `pages`);

        DROP FUNCTION IF EXISTS semester_start;
        DELIMITER $$
        CREATE FUNCTION semester_start (d date) RETURNS date
                DETERMINISTIC
                BEGIN
                IF MONTH(d) > 8 THEN
                    RETURN MAKEDATE(YEAR(d), 213);
                ELSE
                        RETURN MAKEDATE(YEAR(d), 1);
                END IF;
            END$$
        DELIMITER ;

        DROP VIEW IF EXISTS jobs_today;
        CREATE VIEW jobs_today AS
            SELECT * FROM jobs
            WHERE DATE(jobs.time) = CURDATE();

        DROP VIEW IF EXISTS refunds_today;
        CREATE VIEW refunds_today AS
            SELECT * FROM refunds
            WHERE DATE(refunds.time) = CURDATE();

        DROP VIEW IF EXISTS printed_today;
        CREATE VIEW `printed_today` AS
            SELECT
                jobs.user AS user,
                COALESCE(SUM(jobs.pages), 0) - COALESCE(SUM(refunds.pages), 0) AS today
            FROM jobs_today AS jobs
            LEFT OUTER JOIN refunds_today AS refunds
            ON jobs.user = refunds.user
            GROUP BY jobs.user
            ORDER BY user;

        DROP VIEW IF EXISTS jobs_semester;
        CREATE VIEW jobs_semester AS
            SELECT * FROM jobs
            WHERE DATE(jobs.time) > semester_start(CURDATE());

        DROP VIEW IF EXISTS refunds_semester;
        CREATE VIEW refunds_semester AS
            SELECT * FROM refunds
            WHERE DATE(refunds.time) > semester_start(CURDATE());

        DROP VIEW IF EXISTS printed_semester;
        CREATE VIEW `printed_semester` AS
            SELECT
                jobs.user AS user,
                COALESCE(SUM(jobs.pages), 0) - COALESCE(SUM(refunds.pages), 0) AS semester
            FROM jobs_semester AS jobs
            LEFT OUTER JOIN refunds_semester AS refunds
            ON jobs.user = refunds.user
            GROUP BY jobs.user
            ORDER BY user;

        DROP VIEW IF EXISTS printed;
        CREATE VIEW `printed` AS
            SELECT
                printed_today.user AS user,
                printed_today.today AS today,
                printed_semester.semester AS semester
            FROM printed_today
            RIGHT OUTER JOIN printed_semester
            ON printed_today.user = printed_semester.user
            ORDER BY user;

        GRANT SELECT ON `ocfprinting`.`printed` TO 'anonymous'@'%';
        ''',
    )
    return schema
