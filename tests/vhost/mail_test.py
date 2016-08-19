import mock
import pkg_resources
import pytest

import ocflib.vhost.mail
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


def test_add_and_remove_addresses(
        mysql_connection,
        example_vhost,
        another_example_vhost,
):
    assert example_vhost.get_forwarding_addresses(mysql_connection) == set()

    addr1 = MailForwardingAddress(
        'ckuehl@dev-vhost.ocf.berkeley.edu',
        'hunter2',
        'ckuehl@ocf.berkeley.edu',
        None,
    )
    addr2 = MailForwardingAddress(
        '@dev-vhost.ocf.berkeley.edu',
        None,
        'ckuehl@ocf.berkeley.edu',
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


@pytest.yield_fixture
def mysql_connection(mysql_database):
    mysql_database.run_cli_query(
        pkg_resources.resource_string('ocflib.vhost', 'ocfmail.sql'),
    )
    with mysql_database.connection() as c:
        yield c
