import string
from base64 import b64encode
from contextlib import contextmanager
from itertools import chain
from textwrap import dedent

import ldap3
import pexpect

import ocflib.constants as constants
from ocflib.misc.mail import send_problem_report


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
    return ldap_connection(constants.OCF_LDAP)


def ldap_ucb():
    """Context manager that provides an ldap3 Connection to the campus LDAP.

    Example usage:

       with ldap_ucb() as c:
            c.search(UCB_LDAP_PEOPLE, '(uid=ckuehl)', attributes=['uidNumber'])
    """
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
    """
    # LDAP attributes can have multiple values, but commonly we don't consider
    # that. So, let's sanity check the types we've received.
    for v in attributes.values():
        assert type(v) in (list, tuple), 'Value must be list or tuple.'

    def format_attr(key, values):
        # might be possible to have non-ASCII letters in keys, but don't think
        # it will happen to us. we can fix this if it ever does.
        assert all(c in string.ascii_letters for c in key), 'key is not ASCII letters'

        # rather than try to carefully escape values, we just base64 encode
        return (
            '{key}:: {value}'.format(
                key=key,
                value=b64encode(value.encode('utf8')).decode('ascii'),
            ) for value in values
        )

    lines = list(chain(
        format_attr('dn', [dn]),
        *(format_attr(key, values) for key, values in attributes.items())
    ))

    cmd = 'kinit -t {keytab} {principal} ldapadd'.format(
        keytab=keytab,
        principal=admin_principal,
    )

    child = pexpect.spawn(cmd, timeout=10)
    child.expect('SASL data security layer installed.')

    for line in lines:
        child.sendline(line)

    child.sendeof()
    child.expect('adding new entry "{dn}"'.format(dn=dn))
    child.expect(pexpect.EOF)

    output_after_adding = child.before.decode('utf8').strip()

    if 'Already exists (68)' in output_after_adding:
        raise ValueError('DN already exists, this is a duplicate.')

    if output_after_adding != '':
        send_problem_report(
            dedent(
                '''\
                Unknown problem occured when trying to add LDAP entry; the code
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
