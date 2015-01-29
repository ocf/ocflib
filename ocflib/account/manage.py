"""Module containing account management methods, such as password changing,
account creation, etc."""

import base64
import fcntl
import getpass
import paramiko
import pexpect
import socket
from datetime import date

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

import ocflib.account.search as search
import ocflib.account.validators as validators
import ocflib.constants as constants
import ocflib.misc.mail as mail
import ocflib.misc.shell as shell
import ocflib.misc.validators


def change_password_with_staffer(username, password, principal,
                                 admin_password):
    """Change a user's Kerberos password using kadmin and a password, subject
    to username and password validation."""
    validators.validate_username(username)
    validators.validate_password(username, password)

    # try changing using kadmin pexpect
    cmd = "{kadmin_path} -p {principal} cpw {username}".format(
        kadmin_path=shell.escape_arg(constants.KADMIN_PATH),
        principal=shell.escape_arg(principal),
        username=shell.escape_arg(username))

    child = pexpect.spawn(cmd, timeout=10)

    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(username))
    child.sendline(password)
    child.expect("Verify password - {}@OCF.BERKELEY.EDU's Password:"
                 .format(username))
    child.sendline(password)

    # now give admin principal password
    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(principal))
    child.sendline(admin_password)

    child.expect(pexpect.EOF)

    output = child.before.decode('utf8')
    if "Looping detected" in output:
        raise ValueError("Invalid admin password given.")
    elif "kadmin" in output:
        raise ValueError("kadmin Error: {}".format(output))

    _notify_password_change(username)


def change_password_with_keytab(username, password, keytab, principal):
    """Change a user's Kerberos password using a keytab, subject to username
    and password validation."""
    validators.validate_username(username, check_exists=True)
    validators.validate_password(username, password)

    # try changing using kadmin pexpect
    cmd = "{kadmin_path} -K {keytab} -p {principal} cpw {username}".format(
        kadmin_path=shell.escape_arg(constants.KADMIN_PATH),
        keytab=shell.escape_arg(keytab),
        principal=shell.escape_arg(principal),
        username=shell.escape_arg(username))

    child = pexpect.spawn(cmd, timeout=10)

    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(username))
    child.sendline(password)
    child.expect("Verify password - {}@OCF.BERKELEY.EDU's Password:"
                 .format(username))
    child.sendline(password)

    child.expect(pexpect.EOF)

    output = child.before.decode('utf8')
    if "kadmin" in output:
        raise ValueError("kadmin Error: {}".format(output))

    _notify_password_change(username)


def _notify_password_change(username):
    """Send email about a password change."""

    name = search.user_attrs(username)['cn'][0]
    body = """Howdy there {name},

Just a quick heads up that your Open Computing Facility account password was
just reset, hopefully by you.

As a a reminder, your OCF username is: {username}

If you're not sure why this happened, please reply to this email ASAP.

{signature}""".format(name=name,
                      username=username,
                      signature=constants.MAIL_SIGNATURE)

    mail.send_mail_user(username, "[OCF] Account password changed", body)


def trigger_create(ssh_key_path, host_keys_path):
    """Attempt to trigger a create run on the admin server."""

    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(host_keys_path)
    ssh.connect(hostname='admin.ocf.berkeley.edu', username='atool', pkey=key)
    ssh.exec_command('/srv/atool/bin/create')


def encrypt_password(password):
    """Encrypts (not hashes) a user password to be stored on disk while it
    awaits approval.

    Generate the public / private keys with the following code:
    >>> from Crypto.PublicKey import RSA
    >>> key = RSA.generate(2048)
    >>> open("private.pem", "w").write(key.exportKey())
    >>> open("public.pem", "w").write(key.publickey().exportKey())
    """
    # TODO: is there any way we can save the hash instead? this is tricky
    # because we need to stick it in kerberos, but this is bad as-is...
    key = RSA.importKey(open(constants.CREATE_PUBKEY_PATH).read())
    RSA_CIPHER = PKCS1_OAEP.new(key)
    return RSA_CIPHER.encrypt(password)


def queue_creation(full_name, calnet_uid, callink_oid, username, email,
                   password, responsible=None):
    """Queues a user account for creation."""

    # individuals should have calnet_uid, groups should have callink_oid
    if calnet_uid and callink_oid:
        raise ValueError("Only one of calnet_uid or callink_oid may be set.")

    # callink_oid might be 0, which is OK (indicates non-RSO group)
    if not calnet_uid and callink_oid is None:
        raise ValueError("One of calnet_uid or callink_oid must be set.")

    validators.validate_username(username)
    validators.validate_password(username, password)

    if validators.user_exists(username):
        raise ValueError("Username {} is already taken.".format(username))

    if validators.username_queued(username):
        raise ValueError(
            "Username {} is queued for creation.".format(username))

    if validators.username_reserved(username):
        raise ValueError("Username {} is reserved.".format(username))

    full_name = ''.join(c for c in full_name if c.isalpha() or c == ' ')

    if len(full_name) < 3:
        raise ValueError("Full name should be >= 3 characters.")

    if not ocflib.misc.validators.valid_email(email):
        raise ValueError("Email is invalid.")

    # actually create the account
    password = base64.b64encode(encrypt_password(
        password.encode("utf8"))).decode('ascii')

    # TODO: replace this with a better format
    entry_record = [
        username,
        full_name if calnet_uid else '(null)',  # name IF not group
        full_name if not calnet_uid else '(null)',  # name IF group
        email,
        0,
        0 if calnet_uid else 1,
        password,
        calnet_uid or callink_oid,  # university ID
        responsible or '(null)'
    ]

    # same as entry_record but without password
    entry_log = entry_record[:6] + entry_record[7:] + \
        [date.today().isoformat(), getpass.getuser(), socket.getfqdn()]

    # write record to queue and log
    save = (
        (constants.QUEUED_ACCOUNTS_PATH, entry_record),
        (constants.CREATE_LOG_PATH, entry_log)
    )

    for path, entry in save:
        with open(path, 'a') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            print(':'.join(map(str, entry)), file=f)
            fcntl.flock(f, fcntl.LOCK_UN)
