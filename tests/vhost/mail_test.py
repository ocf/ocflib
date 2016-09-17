import crypt

import mock
import pkg_resources
import pytest

import ocflib.vhost.mail
from ocflib.vhost.mail import crypt_password
from ocflib.vhost.mail import get_mail_vhosts
from ocflib.vhost.mail import MailForwardingAddress
from ocflib.vhost.mail import MailVirtualHost
from ocflib.vhost.mail import vhosts_for_user


@pytest.fixture
def example_vhost():
    return MailVirtualHost('staff', 'dev-vhost.ocf.berkeley.edu')


@pytest.fixture
def another_example_vhost():
    return MailVirtualHost('staff', 'vhost.berkeley.edu')


@pytest.yield_fixture
def fake_vhosts():
    text = (
        '# this is a comment at the start     \n',
        '  # this is a comment with leading whitespace\n',
        '\n',
        '\n',
        '           \n',
        'staff dev-vhost.ocf.berkeley.edu  \n',
        'staff    dev-dev-vhost.ocf.berkeley.edu\n',
        'ckuehl\tckuehl.berkeley.edu\n',
        '\n',
        '# sup another comment\n',
        'daradib   \t daradib.wat \n',
        '\n',
    )
    with mock.patch.object(ocflib.vhost.mail, 'get_mail_vhost_db', return_value=text):
        yield


@pytest.mark.usefixtures('fake_vhosts')
def test_get_mail_vhosts():
    assert get_mail_vhosts() == {
        MailVirtualHost('staff', 'dev-vhost.ocf.berkeley.edu'),
        MailVirtualHost('staff', 'dev-dev-vhost.ocf.berkeley.edu'),
        MailVirtualHost('ckuehl', 'ckuehl.berkeley.edu'),
        MailVirtualHost('daradib', 'daradib.wat'),
    }


@pytest.mark.usefixtures('fake_vhosts')
def test_vhosts_for_user():
    assert vhosts_for_user('staff') == {
        MailVirtualHost('staff', 'dev-vhost.ocf.berkeley.edu'),
        MailVirtualHost('staff', 'dev-dev-vhost.ocf.berkeley.edu'),
    }
    assert vhosts_for_user('ckuehl') == {
        MailVirtualHost('ckuehl', 'ckuehl.berkeley.edu'),
    }
    assert vhosts_for_user('jvperrin') == set()


def _normalize_times(addrs):
    return {
        addr._replace(last_updated=None)
        for addr in addrs
    }


@pytest.mark.parametrize(('forward_to', 'expected'), (
    ('a@a.com,b@b.com', {'a@a.com', 'b@b.com'}),
    (' a@a.com  , b@b.com ', {'a@a.com', 'b@b.com'}),
    (', a@a.com  ,', {'a@a.com'}),
    ('', set()),
    (' ', set()),
    (' , , ', set()),
))
def test_get_forwarding_addresses_forward_to_parsing(
        forward_to,
        expected,
        example_vhost,
):
    """Make sure we're a little tolerant in forward_to parsing."""
    fake_connection = mock.Mock(
        __iter__=lambda _: iter(({
            'address': 'test@test.com',
            'password': None,
            'forward_to': forward_to,
            'last_updated': None,
        },))
    )
    result, = example_vhost.get_forwarding_addresses(fake_connection)
    assert result.forward_to == expected


def test_add_and_remove_addresses(
        mysql_connection,
        example_vhost,
        another_example_vhost,
):
    assert example_vhost.get_forwarding_addresses(mysql_connection) == set()

    addr1 = MailForwardingAddress(
        'ckuehl@dev-vhost.ocf.berkeley.edu',
        'hunter2',
        frozenset(['ckuehl@ocf.berkeley.edu']),
        None,
    )
    addr2 = MailForwardingAddress(
        '@dev-vhost.ocf.berkeley.edu',
        None,
        frozenset(['ckuehl@ocf.berkeley.edu', 'daradib@ocf.berkeley.edu']),
        None,
    )

    # add one-by-one
    example_vhost.add_forwarding_address(mysql_connection, addr1)
    assert _normalize_times(example_vhost.get_forwarding_addresses(mysql_connection)) == {addr1}

    example_vhost.add_forwarding_address(mysql_connection, addr2)
    assert _normalize_times(example_vhost.get_forwarding_addresses(mysql_connection)) == {addr1, addr2}

    # unrelated vhost should have no addresses
    assert another_example_vhost.get_forwarding_addresses(mysql_connection) == set()

    # now remove them
    example_vhost.remove_forwarding_address(
        mysql_connection,
        'ckuehl@dev-vhost.ocf.berkeley.edu',
    )
    assert _normalize_times(example_vhost.get_forwarding_addresses(mysql_connection)) == {addr2}

    example_vhost.remove_forwarding_address(
        mysql_connection,
        '@dev-vhost.ocf.berkeley.edu',
    )
    assert example_vhost.get_forwarding_addresses(mysql_connection) == set()


@pytest.mark.parametrize('password', [
    '',
    'correct horse battery staple',
    'hunter2',
    '12yuCV*()AYY!@)+R*_yf9-()@#$)_&!YU($12\'"!#$!@)[]}\\',
])
def test_crypt_password(password):
    crypted = crypt_password(password)

    # it should be a sha512 hash
    assert crypted.startswith('$6$')

    # verify password against hash succeeds
    assert crypt.crypt(password, crypted) == crypted

    # verify not-the-password against hash fails
    for not_password in ['', password + ' ', 'hunter3']:
        assert crypt.crypt(password, crypt_password(not_password)) != crypted


def test_mail_forwarding_address_is_wildcard():
    assert MailForwardingAddress('@vhost.com', None, frozenset(), None).is_wildcard
    assert not MailForwardingAddress('bob@vhost.com', None, frozenset(), None).is_wildcard


@pytest.yield_fixture
def mysql_connection(mysql_database):
    mysql_database.run_cli_query(
        pkg_resources.resource_string('ocflib.vhost', 'ocfmail.sql'),
    )
    with mysql_database.connection() as c:
        yield c
