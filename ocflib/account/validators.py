import difflib
import pwd
import string
import sys

import cracklib

import ocflib.constants as constants
import ocflib.misc.mail


def validate_username(username, check_exists=False):
    """Validate a username, raising a descriptive exception if problems are
    encountered."""

    if username_reserved(username):
        raise ValueError('Username is reserved')

    if not 3 <= len(username) <= 16:
        raise ValueError('Username must be between 3 and 16 characters')

    if not all(c.islower() for c in username):
        raise ValueError('Username must be all lowercase letters')

    if check_exists and not user_exists(username):
        raise ValueError('Username does not exist')


def validate_password(username, password, strength_check=True):
    """Validate a password, raising a descriptive exception if problems are
    encountered. Optionally checks password strength."""

    if strength_check:
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters')

        s = difflib.SequenceMatcher()
        s.set_seqs(password, username)

        if s.ratio() > 0.6:
            raise ValueError('Password is too similar to username')

        try:
            cracklib.VeryFascistCheck(password)
        except ValueError as e:
            raise ValueError('Password problem: {}'.format(e))

    # sanity check; note we don't use string.whitespace since we don't want
    # tabs or newlines
    allowed = string.digits + string.ascii_letters + string.punctuation + ' '

    if not all(c in allowed for c in password):
        raise ValueError('Password contains forbidden characters')


# TODO: we have two implementations of this (one here, one in search).
# one should be removed.
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

    if username in constants.RESERVED_USERNAMES:
        return True

    # sanity check: make sure no local users share the username
    with open('/etc/passwd') as f:
        if any(line.startswith(username + ':') for line in f):
            print(
                'WARNING: Username {} rejected based on /etc/passwd!'
                .format(username),
                file=sys.stderr)
            ocflib.misc.mail.send_problem_report(
                """Username {} rejected based on /etc/passwd. It should be \
added to RESERVED_USERNAMES for consistency across \
servers!""".format(username))
            return True

    return False
