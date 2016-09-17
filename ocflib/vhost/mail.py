import crypt
from collections import namedtuple

import pymysql
import requests
from cached_property import cached_property


VHOST_MAIL_DB_PATH = '/home/s/st/staff/vhost/vhost-mail.conf'
VHOST_MAIL_DB_URL = 'https://www.ocf.berkeley.edu/~staff/vhost-mail.conf'


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
    """Returns lines from the vhost database. Loaded from the filesystem (if
    available), or from the web if not."""
    try:
        with open(VHOST_MAIL_DB_PATH) as f:
            return list(map(str.strip, f))
    except IOError:
        # fallback to database loaded from web
        return requests.get(VHOST_MAIL_DB_URL).text.split('\n')


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


def get_connection(user, password, db='ocfmail', **kwargs):
    """Return a connection to MySQL."""
    return pymysql.connect(
        user=user,
        password=password,
        db=db,
        host='mysql.ocf.berkeley.edu',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        **dict({'autocommit': True}, **kwargs)
    )
