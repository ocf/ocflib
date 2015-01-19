import difflib
import pwd
import string

import cracklib

import ocflib.constants as constants

def validate_username(username):
    """Validate a username, raising a descriptive exception if problems are
    encountered."""
    # TODO: is the username reserved?

    if not 3 <= len(username) <= 8:
        raise Exception("Username must be between 3 and 8 characters")

    if not all(c.islower() for c in username):
        raise Exception("Username must be all lowercase letters")

def validate_password(username, password):
    """Validate a password, raising a descriptive exception if problems are
    encountered."""

    if len(password) < 8:
        raise Exception("Password must be at least 8 characters")

    s = difflib.SequenceMatcher()
    s.set_seqs(password, username)

    if s.ratio() > 0.6:
        raise Exception("Password is too similar to username")

    if not all(c in string.printable for c in password):
        raise Exception("Password contains forbidden characters")

    try:
        cracklib.FascistCheck(password)
    except ValueError as e:
        raise Exception("Password problem: {0}".format(e))

def user_exists(username):
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False
    else:
        return True

def username_reserved(username):
    if username.startswith('ocf'):
        return True
    return username in constants.RESERVED_USERNAMES

def username_queued(username):
    """Returns if the username has already been requested and is queued to be
    created."""
    with open(constants.QUEUED_ACCOUNTS_PATH) as f:
        return any(line.startswith(username + ":") for line in f)
