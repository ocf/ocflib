import subprocess
from base64 import b64encode
from contextlib import contextmanager
from datetime import datetime
from itertools import chain
from textwrap import dedent

import ldap3

from ocflib.misc.mail import send_problem_report

# ocf ldap
OCF_LDAP = 'ldap.ocf.berkeley.edu'
OCF_LDAP_URL = 'ldaps://' + OCF_LDAP
OCF_LDAP_PEOPLE = 'ou=People,dc=OCF,dc=Berkeley,dc=EDU'
OCF_LDAP_HOSTS = 'ou=Hosts,dc=OCF,dc=Berkeley,dc=EDU'
OCF_LDAP_GROUP = 'ou=Group,dc=OCF,dc=Berkeley,dc=EDU'


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

    lines = [
        '{key}:: {value}'.format(
            key=key,
            value=b64encode(format_value(value).encode('utf8')).decode('ascii'),
        ) for value in values
    ]

    return lines


def _write_ldif(lines, dn, keytab=None, admin_principal=None):
    """Issue an update to LDAP via ldapmodify in the form of lines of an LDIF
    file. This could be a new addition to LDAP, a modification of an existing
    item, or even a deletion depending on the changetype attribute given as
    part of the sequence of lines.

    :param lines: ldif file as a sequence of lines

    A ldif file looks something like this:

        dn: uid=jvperrin,ou=People,dc=OCF,dc=Berkeley,dc=EDU
        changetype: modify
        replace: loginShell
        loginShell: /bin/zsh

    It specifies the record or records to change, the type of change, and the
    changes to make. To handle special characters (e.g. anything unprintable)
    we base64-encode the dn and the values we set to get something more like
    this (note the two colons instead of one to designate base64 data):

        dn:: dWlkPWp2cGVycmluLG91PVBlb3BsZSxkYz1PQ0YsZGM9QmVya2VsZXksZGM9RURV
        changetype: modify
        replace: loginShell
        loginShell:: L2Jpbi96c2g=
    """

    # Authenticate if these options are given. Otherwise, assume that
    # authentication has already been done and that a valid kerberos ticket
    # for the current user already exists
    if keytab and admin_principal:
        command = ('/usr/bin/kinit', '-t', keytab, admin_principal, '/usr/bin/ldapmodify', '-Q')
    else:
        command = ('/usr/bin/ldapmodify', '-Q')

    try:
        subprocess.check_output(
            command,
            input='\n'.join(lines),
            universal_newlines=True,
            timeout=10,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 32:
            raise ValueError('Tried to modify nonexistent entry.')
        elif e.returncode == 68:
            raise ValueError('Tried to create duplicate entry.')
        else:
            send_problem_report(
                dedent(
                    '''\
                    Unknown problem occured when trying to write to LDAP; the
                    code should be updated to handle this case.

                    dn: {dn}
                    keytab: {keytab}
                    principal: {principal}

                    Error code: {returncode}

                    Unexpected output:
                    {output}

                    Lines passed to ldapmodify:
                    {lines}
                    '''
                ).format(
                    dn=dn,
                    keytab=keytab,
                    principal=admin_principal,
                    returncode=e.returncode,
                    output=e.output,
                    lines='\n'.join('    ' + line for line in lines)
                )
            )
            raise ValueError('Unknown LDAP failure was encountered.')


def create_ldap_entry(
    dn,
    attributes,
    **kwargs  # TODO: Add a trailing comma here in Python 3.6+
):
    """Creates an LDAP entry by shelling out to ldapadd.

    :param dn: distinguished name of the new entry
    :param attributes: dict mapping attribute name to list of values
    :param **kwargs: any additional keyword arguments to pass on to _write_ldif
    """
    lines = chain(
        _format_attr('dn', [dn]),
        ('changetype: add',),
        *(_format_attr(key, values) for key, values in sorted(attributes.items()))
    )

    _write_ldif(lines, dn, **kwargs)


def modify_ldap_entry(
    dn,
    attributes,
    **kwargs  # TODO: Add a trailing comma here in Python 3.6+
):
    """Modifies the attributes of an existing LDAP entry by shelling out to
    ldapmodify.

    Existing attributes will be overwritten by the new values, and new
    attributes will be created as needed.

    :param dn: distinguished name of the entry to modify
    :param attributes: dict mapping attribute name to list of values
    :param **kwargs: any additional keyword arguments to pass on to _write_ldif
    """
    lines = chain(
        _format_attr('dn', [dn]),
        ('changetype: modify',),
        *(
            chain(
                ('replace: {}'.format(key),),
                _format_attr(key, values),
                ('-',),
            ) for key, values in sorted(attributes.items())
        )
    )

    _write_ldif(lines, dn, **kwargs)


def format_timestamp(timestamp):
    """Returns a string representing a python datetime in LDAP timestamp
    format.

    :param timestamp: An "aware" datetime object
    :return: A timestamp in the format YYYYMMDDhhmmss-0700 (or -0800 in the winter)
    """
    if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        raise ValueError('Timestamp has no timezone info')
    return timestamp.strftime('%Y%m%d%H%M%S%z')
