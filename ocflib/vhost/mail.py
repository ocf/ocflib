from collections import namedtuple

import pymysql
import requests


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
                forward_to=r['forward_to'],
                last_updated=r['last_updated'],
            )
            for r in c
        }

    def add_forwarding_address(self, c, addr):
        c.execute(
            'INSERT INTO `addresses`'
            '(`address`, `password`, `forward_to`)'
            'VALUES (%s, %s, %s)',
            (addr.address, addr.crypt_password, addr.forward_to),
        )

    def remove_forwarding_address(self, c, addr):
        c.execute(
            'DELETE FROM `addresses`'
            'WHERE `address` = %s',
            (addr,),
        )


MailForwardingAddress = namedtuple('MailForwardingAddress', (
    'address',
    'crypt_password',
    'forward_to',
    'last_updated',
))


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
