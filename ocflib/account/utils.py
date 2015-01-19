"""Random account methods that don't fit anywhere else."""
import pexpect

import ocflib.account.validators as validators


def password_matches(username, password):
    """Returns True if the password matches the user account given"""

    validators.validate_username(username)
    validators.validate_password(username, password, strength_check=False)

    if not validators.user_exists(username):
        raise Exception("User doesn't exist")

    cmd = "kinit --no-forwardable -l0 {}@OCF.BERKELEY.EDU".format(username)
    child = pexpect.spawn(cmd, timeout=10)

    child.expect("{}@OCF.BERKELEY.EDU's Password:".format(username))
    child.sendline(password)

    child.expect(pexpect.EOF)
    child.close()

    return child.exitstatus == 0
