import string
from base64 import b64encode
from contextlib import contextmanager
from datetime import datetime
from itertools import chain
from textwrap import dedent

import ldap3
import pexpect

from ocflib.misc.mail import send_problem_report

# ocf ldap
OCF_LDAP = 'ldap.ocf.berkeley.edu'
OCF_LDAP_URL = 'ldaps://' + OCF_LDAP
OCF_LDAP_PEOPLE = 'ou=People,dc=OCF,dc=Berkeley,dc=EDU'
OCF_LDAP_HOSTS = 'ou=Hosts,dc=OCF,dc=Berkeley,dc=EDU'


# university ldap
UCB_LDAP = 'ldap.berkeley.edu'
UCB_LDAP_URL = 'ldaps://' + UCB_LDAP
UCB_LDAP_PEOPLE = 'ou=People,dc=Berkeley,dc=EDU'


@contextmanager
def ldap_connection(host):
    """Context manager that provides an ldap3 Connection.

    Example usage:

       with ldap_connection('ldap.ocf.berkeley.edu') as c:
            c.search(OCF_LDAP_PEOPLE, '(uid=ckuehl)', attributes=['uidNumber'])

    You might find it more convenient to use the ldap_ocf or ldap_ucb functions
    also defined.

    :param host: server hostname
    """
    server = ldap3.Server(host, use_ssl=True)
    with ldap3.Connection(server) as connection:
        yield connection


def ldap_ocf():
    """Context manager that provides an ldap3 Connection to OCF's LDAP server.

    Example usage:

       with ldap_ocf() as c:
            c.search(OCF_LDAP_PEOPLE, '(uid=ckuehl)', attributes=['uidNumber'])
    """
    return ldap_connection(OCF_LDAP)


def ldap_ucb():
    """Context manager that provides an ldap3 Connection to the campus LDAP.

    Example usage:

       with ldap_ucb() as c:
            c.search(UCB_LDAP_PEOPLE, '(uid=ckuehl)', attributes=['uidNumber'])
    """
    return ldap_connection(UCB_LDAP)


def _format_attr(key, values):
    # Unfortunately, LDIF is a string format while we deal in python types, so
    # everything must be converted at some point.
    def format_value(value):
        return format_timestamp(value) if isinstance(value, datetime) else str(value)

    # Some LDAP attributes can have multiple values while most are single-
    # valued, so we handle both cases.
    if not type(values) in (list, tuple):
        values = (values,)

    # might be possible to have non-ASCII letters in keys, but don't think
    # it will happen to us. we can fix this if it ever does.
    assert all(c in string.ascii_letters for c in key), 'key is not ASCII letters'

    lines = [
        '{key}:: {value}'.format(
            key=key,
            value=b64encode(format_value(value).encode('utf8')).decode('ascii'),
        ) for value in values
    ]

    return lines


def _write_ldif(lines, dn, keytab, admin_principal):
    """Issue an update to LDAP via ldapmodify in the form of lines of an LDIF
    file.

    :param lines: ldif file as a sequence of lines
    """

    cmd = 'kinit -t {keytab} {principal} ldapmodify'.format(
        keytab=keytab,
        principal=admin_principal,
    )

    child = pexpect.spawn(cmd, timeout=10)
    child.expect('SASL data security layer installed.')

    for line in lines:
        child.sendline(line)

    child.sendeof()
    child.expect('entry "{}"'.format(dn))
    child.expect(pexpect.EOF)

    output_after_adding = child.before.decode('utf8').strip()

    if 'Already exists (68)' in output_after_adding:
        raise ValueError('Tried to create duplicate entry.')
    elif 'No such object (32)' in output_after_adding:
        raise ValueError('Tried to modify nonexistent entry.')

    if output_after_adding != '':
        send_problem_report(
            dedent(
                '''\
                Unknown problem occured when trying to write to LDAP; the code
                should be updated to handle this case.

                dn: {dn}
                keytab: {keytab}
                principal: {principal}

                Unexpected output:
                {output_after_adding}

                Lines passed to ldapadd:
                {lines}
                '''
            ).format(
                dn=dn,
                keytab=keytab,
                principal=admin_principal,
                output_after_adding=output_after_adding,
                lines='\n'.join('    ' + line for line in lines)
            )
        )
        raise ValueError('Unknown LDAP failure was encountered.')


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
    """
    lines = chain(
        _format_attr('dn', [dn]),
        ('changetype: add',),
        *(_format_attr(key, values) for key, values in attributes.items())
    )

    _write_ldif(lines, dn, keytab, admin_principal)


def modify_ldap_entry_with_keytab(
    dn,
    attributes,
    keytab,
    admin_principal,
):
    """Modifies the attributes of an existing LDAP entry by shelling out to
    ldapmodify.

    Existing attributes will be overwritten by the new values, and new
    attributes will be created as needed.

    :param dn: distinguished name of the entry to modify
    :param attributes: dict mapping attribute name to list of values
    :param keytab: path to the admin keytab
    :param admin_principal: admin principal to use with the keytab
    """
    lines = chain(
        _format_attr('dn', [dn]),
        ('changetype: modify',),
        *(
            chain(
                ('replace: {}'.format(key),),
                _format_attr(key, values),
                ('-',),
            ) for key, values in attributes.items()
        )
    )

    _write_ldif(lines, dn, keytab, admin_principal)


def format_timestamp(timestamp):
    """Returns a string representing a python datetime in LDAP timestamp
    format.

    :param timestamp: An "aware" datetime object
    :return: A timestamp in the format YYYYMMDDhhmmss-0700 (or -0800 in the winter)
    """
    if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        raise ValueError('Timestamp has no timezone info')
    return timestamp.strftime('%Y%m%d%H%M%S%z')
