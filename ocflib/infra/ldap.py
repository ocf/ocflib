from contextlib import contextmanager

import ldap3

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


def create_ldap_entry_with_keytab(
    dn,
    attributes,
    keytab,
    admin_principal,
):
    """Creates an LDAP entry by shelling out to ldapadd.

    :param dn: distinguished name of the new entry
    :param attributes: dict mapping attribute name to list of values
    :param keytab: path to the admin keytab
    :param admin_principal: admin principal to use with the keytab
    :return: the password of the newly-created account
    """
    # LDAP attributes can have multiple values, but commonly we don't consider
    # that. So, let's sanity check the types we've received.
    for v in attributes.values():
        assert type(v) in (list, tuple), 'Value must be list or tuple.'

    # TODO: implement this
    raise NotImplementedError()
