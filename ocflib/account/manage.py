"""Module containing account management methods, such as password changing,
account creation, etc."""

import base64
import fcntl
import getpass
import paramiko
import pexpect
import socket
import time

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

# TODO: adjust this import
from ocf.utils import clean_user_account, clean_password
import kerberos

def change_password(user_account, new_password):
    """Change a user's Kerberos password.

    Runs a kadmin command in a pexpect session to change a user's password.

    Args:
        user_account: a dirty string of a user's OCF account
        new_password: a dirty string of a user's new password

    Returns:
        True if successful

    Raises:
        Exception: kadmin returned an error. Probably incorrect
            principal or error with sending the new password.
        pexpect.TIMEOUT: We never got the line that we were expecting,
            so something probably went wrong with the lines that we sent.
        pexpect.EOF: The child ended prematurely.

    """

    # TODO: don't clean these, error if bad instead
    user_account = clean_user_account(user_account)
    new_password = clean_password(new_password)
    cmd = kerberos._kadmin_command(user_account)
    child = pexpect.spawn(cmd, timeout=10)

    child.expect("%s@OCF.BERKELEY.EDU's Password:" % user_account)
    child.sendline(new_password)

    child.expect("Verify password - %s@OCF.BERKELEY.EDU's Password:" % user_account)
    child.sendline(new_password)

    child.expect(pexpect.EOF)
    if "kadmin" in child.before:
        raise Exception("kadmin Error: %s" % child.before)

    return True

def _trigger_create():
    """Attempt to trigger a create run."""
    key = paramiko.RSAKey.from_private_key_file(settings.ADMIN_SSH_KEY)
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(settings.CMDS_HOST_KEYS_FILENAME)
    ssh.connect(hostname='admin.ocf.berkeley.edu', username='atool', pkey=key)
    ssh.exec_command('/srv/atool/bin/create')

def _encrypt_password(password):
    # Use an asymmetric encryption algorithm to allow the keys to be stored on disk
    # Generate the public / private keys with the following code:
    # >>> from Crypto.PublicKey import RSA
    # >>> key = RSA.generate(2048)
    # >>> open("private.pem", "w").write(key.exportKey())
    # >>> open("public.pem", "w").write(key.publickey().exportKey())

    key = RSA.importKey(open(settings.PASSWORD_PUB_KEY).read())
    RSA_CIPHER = PKCS1_OAEP.new(key)
    return RSA_CIPHER.encrypt(password)

class ApprovalError(Exception):
    pass

# TODO: don't use ApprovalErrors here? or at least fix the imports
def approve_user(real_name, calnet_uid, account_name, email, password):
    _check_real_name(real_name)
    _check_university_uid(calnet_uid)
    _check_username(account_name)
    _check_email(email)
    _check_password(password, real_name)

    _approve(calnet_uid, email, account_name, password, real_name = real_name)

def _approve(university_uid, email, account_name, password, real_name = None,
        responsible = None):

    group_name = "(null)"
    group = 0
    responsible = "(null)"

    # Encrypt the password and base64 encode it
    password = base64.b64encode(_encrypt_password(password.encode()))

    # Write to the list of users to be approved
    sections = [account_name, real_name, group_name,
                email, 0, group, password,
                university_uid, responsible]

    with open(settings.APPROVE_FILE, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(":".join([str(i) for i in sections]) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)

    # Write to the log
    name = real_name

    sections = [account_name, name, university_uid,
                email, getpass.getuser(), socket.gethostname(),
                0, group, time.asctime(), responsible]

    with open(settings.APPROVE_LOG, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(":".join([str(i) for i in sections]) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)

    _trigger_create()
