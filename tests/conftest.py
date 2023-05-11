import os.path
import random
import string
import time
from collections import namedtuple
from subprocess import check_call
from subprocess import PIPE
from subprocess import Popen

import pymysql
import pytest


# To test functions that query UCB LDAP for people, we simply pick
# someone who has a few years before graduating and use their name and
# CalNet UID. Alumni eventually get kicked out of the university's
# "People" OU, so these constants have to be updated every few years
# after the aforementioned party has graduated.
TEST_PERSON_CALNET_UID = 1538112
TEST_PERSON_NAME = 'Frank Dai'


MYSQL_TIMEOUT = 10


@pytest.yield_fixture(scope='session')
def mysqld_socket(tmpdir_factory):
    """Yield a socket to a running MySQL instance."""
    tmpdir = tmpdir_factory.mktemp('var')
    socket = tmpdir.join('socket')
    data_dir = tmpdir.join('data')
    data_dir.ensure_dir()

    check_call((
        os.path.join('/usr', 'bin', 'mysql_install_db'),
        '--no-defaults',
        '--auth-root-authentication-method=normal',
        '--basedir=/usr',
        '--datadir=' + data_dir.strpath,
    ))
    proc = Popen((
        os.path.join('/usr', 'sbin', 'mysqld'),
        '--no-defaults',
        '--skip-networking',
        '--lc-messages-dir', os.path.join('/usr', 'share', 'mysql'),
        '--datadir', data_dir.strpath,
        '--socket', socket.strpath,
    ))

    elapsed = 0
    step = 0.1
    while elapsed < MYSQL_TIMEOUT and not _mysql_ready(socket):
        elapsed += step
        time.sleep(step)

    try:
        yield socket
    finally:
        proc.terminate()
        proc.wait()


def _mysql_ready(socket):
    try:
        get_connection(socket)
    except pymysql.err.OperationalError:
        return False
    else:
        return True


class TemporaryMySQLDatabase(namedtuple('TemporaryMySQLDatabase', (
    'db_name',
    'mysqld_socket',
))):

    def __enter__(self):
        with self.connection(use_db=False) as c:
            c.execute('CREATE DATABASE {};'.format(self.db_name))
        return self

    def __exit__(self, type_, value, tb):
        with self.connection(use_db=False) as c:
            c.execute('DROP DATABASE {};'.format(self.db_name))

    def connection(self, use_db=True):
        kwargs = {}
        if use_db:
            kwargs['db'] = self.db_name
        return get_connection(self.mysqld_socket, **kwargs)

    def run_cli_query(self, query):
        """Run a query using the mysql CLI.

        This is useful because things like delimiters (semicolon) and complex
        statements are hard to write using PyMySQL while still being compatible
        with imports of the schema into the actual database.
        """
        mysql = Popen(
            (
                os.path.join('/usr', 'bin', 'mysql'),
                '-h', 'localhost',
                '-u', 'root',
                '--password=',
                '--database', self.db_name,
                '--socket', self.mysqld_socket.strpath,
            ),
            stdin=PIPE,
        )
        mysql.communicate(query)
        assert mysql.wait() == 0


@pytest.yield_fixture
def mysql_database(mysqld_socket):
    with TemporaryMySQLDatabase(
            db_name='test_' + ''.join(random.choice(string.ascii_lowercase) for _ in range(20)),
            mysqld_socket=mysqld_socket
    ) as d:
        yield d


def get_connection(unix_socket, **kwargs):
    return pymysql.connect(
        unix_socket=unix_socket.strpath,
        user='root',
        password='',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        charset='utf8mb4',
        **kwargs
    )
