from socket import getaddrinfo, gaierror
from difflib import SequenceMatcher
import pwd

from cracklib import FascistCheck

def validate_username_not_reserved(username):
    """Verifies that the username requested is not in the list of reserved names"""
    username_lower = username.lower()
    with open(settings.OCF_RESERVED_NAMES_LIST, "r") as f:
        for reserved_name in f:
            reserved_name = reserved_name.strip().lower()
            if username_lower == reserved_name:
                raise ValidationError("Requested account name is a reserved system name.")

def filter_real_name(name):
    return str(filter(_valid_real_name_char, name))

def _valid_real_name_char(char):
    return char in " -.'" or char.isalpha()

def _check_real_name(real_name):
    if not all(map(_valid_real_name_char, real_name)):
        raise ApprovalError("Invalid characters in name: {0}".format(real_name))

def _check_university_uid(university_uid):
    try:
        int(university_uid)
    except ValueError:
        raise ApprovalError("Invalid UID number: {0}".format(university_uid))

def _check_username(username):

    # Is this a valid username?
    if len(username) > 8 or len(username) < 3:
        raise ApprovalError("Username must be between 3 and 8 letters: {0}".format(username))
    elif any([not i.islower() for i in username]):
        raise ApprovalError("Username must contain only lowercase letters: {0}".format(username))

    # Is the username already taken?
    try:
        pwd.getpwnam(username)
        raise ApprovalError("Username already in use: {0}".format(username))
    except KeyError:
        pass

    # Is the username already requested?
    try:
        with open(settings.APPROVE_FILE) as f:
            for line in f:
                if line.startswith(username + ":"):
                    raise ApprovalError("Username already requested: {0}".format(username))
    except IOError:
        pass

    # Is the username reserved?
    with open(settings.OCF_RESERVED_NAMES_LIST) as reserved:
        for line in reserved:
            if line.strip() == username:
                raise ApprovalError("Username is reserved: {0}".format(username))

def _check_password(password, username):
    if len(password) < 8:
        raise ApprovalError("Password must be at least 8 characters")

    s = SequenceMatcher()
    s.set_seqs(password, username)
    threshold = 0.6
    if s.ratio() > threshold:
        raise ApprovalError("Password is too similar to username")

    # XXX: Double quotes are exploitable when adding through kadmin
    if "\n" in password or "\r" in password:
        raise ApprovalError("Newlines and carriage returns are forbidden in passwords")

    if FascistCheck:
        try:
            FascistCheck(password)
        except ValueError as e:
            raise ApprovalError("Password problem: {0}".format(e))

def clean_user_account(user_account):
    """Return an string that could be an OCF user name"""

    if not user_account:
        return ""

    return "".join(filter(lambda c: c.islower(), [c for c in user_account]))


def clean_password(password):
    """Return a string without tab or newlines"""

    if not password:
        return ""

    password = password.replace("\t", "")
    password = password.replace("\n", "")

    return password

def validate_crack_strength(value):
    try:
        crack.VeryFascistCheck(value)
    except ValueError as e:
        raise ValidationError("Password was too weak.")

def _is_printable_ascii(char):
    return 32 <= ord(char) <= 176

def validate_printable_ascii(value):
    """Verifies that the string value argument is composed only of printable ASCII characters"""

    for char in list(value):
        if not _is_printable_ascii(char):
            raise ValidationError("Password contained characters other than printable ASCII characters.")

def validate_name_characters(name):
    """Only lower-case letters are allowed in names"""
    error = "OCF name contains characters that aren't lower-case letters"
    for char in list(name):
        if not 97 <= ord(char) <= 122:
            # 97 is lower-case "a", 122 is lower-case "z"
            raise ValidationError(error)


def validate_unused_name(name):
    if user_exists(name):
        raise ValidationError("OCF name is already used by someone else")
