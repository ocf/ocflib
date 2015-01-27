import difflib
import pwd
import string

import cracklib

import ocflib.constants as constants


def validate_username(username):
    """Validate a username, raising a descriptive exception if problems are
    encountered."""

    if username_reserved(username):
        raise ValueError("Username is reserved")

    if not 3 <= len(username) <= 8:
        raise ValueError("Username must be between 3 and 8 characters")

    if not all(c.islower() for c in username):
        raise ValueError("Username must be all lowercase letters")


def validate_password(username, password, strength_check=True):
    """Validate a password, raising a descriptive exception if problems are
    encountered. Optionally checks password strength."""

    if strength_check:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        s = difflib.SequenceMatcher()
        s.set_seqs(password, username)

        if s.ratio() > 0.6:
            raise ValueError("Password is too similar to username")

        try:
            cracklib.FascistCheck(password)
        except ValueError as e:
            raise ValueError("Password problem: {}".format(e))

    # sanity check; note we don't use string.whitespace since we don't want
    # tabs or newlines
    allowed = string.digits + string.ascii_letters + string.punctuation + ' '

    if not all(c in allowed for c in password):
        raise ValueError("Password contains forbidden characters")


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
