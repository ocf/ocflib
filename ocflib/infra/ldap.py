import ldap3
from contextlib import contextmanager

import ocflib.constants as constants


@contextmanager
def ldap_connection(host):
    server = ldap3.Server(host, use_ssl=True)
    with ldap3.Connection(server) as connection:
        yield connection


def ldap_ocf():
    return ldap_connection(constants.OCF_LDAP)


def ldap_ucb():
    return ldap_connection(constants.UCB_LDAP)
