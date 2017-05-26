#!/usr/bin/env python3
import os
from collections import namedtuple
from pathlib import Path

import jinja2

from ocflib.account.search import user_is_sorried
from ocflib.misc.mail import email_for_user
from ocflib.vhost.application import get_app_vhosts
from ocflib.vhost.web import get_vhosts


SITE_CFG = '/etc/nginx/sites-enabled/virtual'

LETS_ENCRYPT_SSL = Path('/services/http/ssl')
SSL_BUNDLE = Path('/etc/ssl/apphost')

APP_DIR = Path('/srv/apps')
WEB_DIR = Path('/services/http/users')

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader((
        os.path.abspath(os.path.dirname(__file__)),
    )),
)


class VirtualHost(namedtuple('VirtualHost', (
    'fqdn',
    'user',
    'socket_or_docroot',
    'aliases',
    'flags',
))):
    """A single virtual host as defined by the vhost config files.

    This class defines lots of helper functions which are used in
    generating vhost configuration on the web and app hosts.

    The web and application vhost configs differ only in specifying
    either a socket name or directory to serve. Hence, the two are
    aliased into a single variable whose meaning is differentiated by
    the method used to access it.
    """
    @property
    def socket(self):
        return str(APP_DIR / self.user / (self.socket_or_docroot + '.sock'))

    @property
    def socket_dir(self):
        return str(APP_DIR / self.user)

    @property
    def docroot(self):
        return str(WEB_DIR / self.user[0] / self.user)

    @property
    def contact_email(self):
        return email_for_user(self.user)

    @property
    def dev_alias(self):
        return self.fqdn.replace('.', '-') + '.apphost.ocf.berkeley.edu'

    @property
    def disabled(self):
        return user_is_sorried(self.user)

    @property
    def use_ssl(self):
        return 'nossl' not in self.flags

    @property
    def port(self):
        return 443 if self.use_ssl else 80

    @property
    def ssl_key(self):
        return '/etc/ssl/lets-encrypt/le-vhost.key'

    @property
    def ssl_cert(self):
        return str(LETS_ENCRYPT_SSL / (self.fqdn + '.crt'))

    @property
    def ssl_chain(self):
        return '/etc/ssl/certs/lets-encrypt.crt'

    @property
    def ssl_bundle(self):
        return str(SSL_BUNDLE / (self.fqdn + '.crt'))


def build_web_config():
    """Generates an apache config file for web vhosts from the config
    file."""
    vhosts = set()
    for domain, vhost in get_vhosts().items():
        vhosts.add(VirtualHost(
            fqdn=domain,
            user=vhost['username'],
            socket_or_docroot=vhost['docroot'],
            aliases=tuple(vhost['aliases']),
            flags=tuple(vhost['flags']),
        ))
    tmpl = jinja_env.get_template('vhost-web.jinja')
    return '\n\n'.join(
        tmpl.render(vhost=vhost)
        for vhost in sorted(
            vhosts,
            key=lambda vhost: (vhost.user, vhost.fqdn),
        )
    )


def build_app_config():
    """Generates an nginx config file for app vhosts from the config
    file."""
    vhosts = set()
    for domain, vhost in get_app_vhosts().items():
        vhosts.add(VirtualHost(
            fqdn=domain,
            user=vhost['username'],
            socket_or_docroot=vhost['socket'],
            aliases=tuple(vhost['aliases']),
            flags=tuple(vhost['flags']),
        ))
    tmpl = jinja_env.get_template('vhost-app.jinja')
    return '\n\n'.join(
        tmpl.render(vhost=vhost)
        for vhost in sorted(
            vhosts,
            key=lambda vhost: (vhost.user, vhost.fqdn),
        )
    )
