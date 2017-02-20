import os
import shlex
import string
import subprocess

import pexpect

KADMIN_PATH = '/usr/bin/kadmin'


def create_kerberos_principal_with_keytab(
    principal,
    keytab,
    admin_principal,
    password=None,
):
    """Creates a Kerberos principal by shelling out to kadmin.

    :param principal: name of the principal to create
    :param keytab: path to the admin keytab
    :param admin_principal: admin principal to authenticate with keytab
    :param password: password of the new principal (optional);
                     if not given, defaults to using a random password
    :return: the password of the newly-created account
    """
    # try changing using kadmin pexpect
    cmd = ('{kadmin} -K {keytab} -p {admin} add --use-defaults ' +
           '{principal}').format(
        kadmin=shlex.quote(KADMIN_PATH),
        keytab=shlex.quote(keytab),
        admin=shlex.quote(admin_principal),
        principal=shlex.quote(principal),
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
    child.close()
    if child.exitstatus:
        raise ValueError('kadmin error: {}'.format(output))

    return password


def get_kerberos_principal_with_keytab(principal, keytab, admin_principal):
    """Returns information about an existing kerberos principal.

    Currently, this requires shelling out to kadmin, so the only information
    returned is whether the principal exists.

    :param principal: name of the principal to create
    :param admin_principal: name of the admin principal
    :param keytab: path to the admin keytab
    :return: True if the principal exists, or
             None if the principal does not exist
    """
    cmd = [
        shlex.quote(KADMIN_PATH),
        '-K', shlex.quote(keytab),
        '-p', shlex.quote(admin_principal),
        'get', shlex.quote(principal),
    ]

    try:
        subprocess.check_output(cmd, timeout=10, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if b'Principal does not exist' in e.output:
            return None
        else:
            raise ValueError('kadmin error: {}'.format(e.output))

    return True
