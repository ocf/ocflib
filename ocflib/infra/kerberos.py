import os
import string

import pexpect

from ocflib.constants import KADMIN_PATH
from ocflib.misc.shell import escape_arg


def create_kerberos_principal_with_keytab(
    principal,
    keytab,
    admin_principal,
    password=None,
):
    """Creates a Kerberos principal by shelling out to kadmin.

    :param principal: name of the principal to create
    :param admin_principal: name of the admin principal
    :param keytab: path to the admin keytab
    :param password: password of the new principal (optional);
                     if not given, defaults to using a random password
    :param admin_principal: admin principal to use with the keytab
    :return: the password of the newly-created account
    """
    # try changing using kadmin pexpect
    cmd = ('{kadmin} -K {keytab} -p {admin} add --use-defaults ' +
           '{principal}').format(
        kadmin=escape_arg(KADMIN_PATH),
        keytab=escape_arg(keytab),
        admin=escape_arg(admin_principal),
        principal=escape_arg(principal),
    )

    if not password:
        # XXX: using `--random-password` generates weak passwords, plus spits
        # them to stdout, so we just generate a random one ourselves
        allowed = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(allowed[byte % len(allowed)]
                           for byte in os.urandom(100))

    child = pexpect.spawn(cmd, timeout=10)

    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(principal))
    child.sendline(password)
    child.expect("Verify password - {}@OCF.BERKELEY.EDU's Password:"
                 .format(principal))
    child.sendline(password)

    child.expect(pexpect.EOF)

    output = child.before.decode('utf8')
    if 'kadmin' in output:
        raise ValueError('kadmin Error: {}'.format(output))

    return password
