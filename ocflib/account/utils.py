"""Random account methods that don't fit anywhere else."""

def password_matches(user_account, password):
    """Returns True if the password matches the user account given"""

    user_account = clean_user_account(user_account)
    password = clean_password(password)

    cmd = "kinit --no-forwardable -l0 %s@OCF.BERKELEY.EDU" % user_account
    child = pexpect.spawn(cmd, timeout=10)

    child.expect("%s@OCF.BERKELEY.EDU's Password:" % user_account)
    child.sendline(password)

    child.expect(pexpect.EOF)
    child.close()

    return child.exitstatus == 0

def user_is_group(user_account):
    """Returns True if an OCF user account exists and is a group account"""

    attrs = user_attrs(user_account)
    if 'callinkOid' in attrs or 'oslGid' in attrs:
        return True
