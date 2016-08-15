import random
import string
import time
from collections import namedtuple
from subprocess import check_call
from subprocess import PIPE
from subprocess import Popen

import pymysql
import pytest


MYSQL_TIMEOUT = 10


@pytest.fixture(scope='session')
def mysqld_path(tmpdir_factory):
    """Download and extract a local copy of mysqld."""
    # TODO: let's just install mysql everywhere, lol
    tmpdir = tmpdir_factory.mktemp('mysql')
    with tmpdir.as_cwd():
        check_call(('apt-get', 'download', 'mariadb-server-10.0'))
        check_call(('apt-get', 'download', 'mariadb-server-core-10.0'))
        check_call(('apt-get', 'download', 'mariadb-client-core-10.0'))
        for deb in tmpdir.listdir(lambda f: f.fnmatch('*.deb')):
            check_call(('dpkg', '-x', deb.strpath, '.'))
    return tmpdir


@pytest.yield_fixture(scope='session')
def mysqld_socket(mysqld_path, tmpdir_factory):
    """Yield a socket to a running MySQL instance."""
    tmpdir = tmpdir_factory.mktemp('var')
    socket = tmpdir.join('socket')
    data_dir = tmpdir.join('data')
    data_dir.ensure_dir()

    check_call((
        mysqld_path.join('usr', 'bin', 'mysql_install_db').strpath,
        '--no-defaults',
        '--basedir=' + mysqld_path.join('usr').strpath,
        '--datadir=' + data_dir.strpath,
    ))
    proc = Popen((
        mysqld_path.join('usr', 'sbin', 'mysqld').strpath,
        '--no-defaults',
        '--skip-networking',
        '--lc-messages-dir', mysqld_path.join('usr', 'share', 'mysql').strpath,
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
    'mysqld_path',
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
                self.mysqld_path.join('usr', 'bin', 'mysql').strpath,
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
def mysql_database(mysqld_path, mysqld_socket):
    with TemporaryMySQLDatabase(
            db_name='test_' + ''.join(random.choice(string.ascii_lowercase) for _ in range(20)),
            mysqld_path=mysqld_path,
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
