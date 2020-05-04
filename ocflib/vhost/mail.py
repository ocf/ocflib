import crypt
import functools
from collections import namedtuple

from cached_property import cached_property

from ocflib.infra import mysql

VHOST_MAIL_DB_PATH = '/etc/ocf/vhost-mail.conf'

get_connection = functools.partial(mysql.get_connection, db='ocfmail')


class MailVirtualHost(namedtuple('MailVirtualHost', ('user', 'domain'))):

    def get_forwarding_addresses(self, c):
        """Return list of MailForwardingAddress objects."""
        c.execute(
            'SELECT `address`, `password`, `forward_to`, `last_updated`'
            'FROM `addresses`'
            'WHERE `address` LIKE %s',
            ('%@' + self.domain,),
        )
        return {
            MailForwardingAddress(
                address=r['address'],
                crypt_password=r['password'],
                forward_to=frozenset(addr.strip() for addr in r['forward_to'].split(',') if addr.strip()),
                last_updated=r['last_updated'],
            )
            for r in c
        }

    def add_forwarding_address(self, c, addr):
        # sanity check: forward_to should be a non-empty list-ish
        assert len(addr.forward_to) > 0, addr.forward_to
        assert not isinstance(addr.forward_to, str)

        c.execute(
            'INSERT INTO `addresses`'
            '(`address`, `password`, `forward_to`)'
            'VALUES (%s, %s, %s)',
            (addr.address, addr.crypt_password, ','.join(addr.forward_to)),
        )

    def remove_forwarding_address(self, c, addr):
        c.execute(
            'DELETE FROM `addresses`'
            'WHERE `address` = %s',
            (addr,),
        )


class MailForwardingAddress(namedtuple('MailForwardingAddress', (
    'address',
    'crypt_password',
    'forward_to',
    'last_updated',
))):

    @cached_property
    def is_wildcard(self):
        return self.address.startswith('@')


def get_mail_vhost_db():
    """Returns lines from the vhost config file."""
    with open(VHOST_MAIL_DB_PATH) as f:
        return list(map(str.strip, f))


def get_mail_vhosts():
    """Returns a list of MailVirtualHost objects."""
    vhosts = set()
    for line in get_mail_vhost_db():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        user, domain = line.split()
        vhosts.add(MailVirtualHost(user=user, domain=domain))
    return vhosts


def vhosts_for_user(user):
    """Return MailVirtualHost objects for the user."""
    return {vhost for vhost in get_mail_vhosts() if vhost.user == user}


def crypt_password(password):
    """Return hashed password, compatible with the vhost database."""
    return crypt.crypt(password, salt=crypt.METHOD_SHA512)
