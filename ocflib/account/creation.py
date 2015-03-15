import difflib
import itertools
import math
import os.path
import re
import subprocess
import sys

import ocflib.account.search as search
import ocflib.account.utils as utils
import ocflib.constants as constants
import ocflib.misc.mail as mail
import ocflib.validators as validators


def create_home_dir(user):
    """Create home directory for user. Makes a directory with appropriate
    permissions, then copies in OCF's skeleton dotfiles."""

    home = utils.home_dir(user['account_name'])
    subprocess.check_call(
        ['sudo', 'install', '-d', '--mode=0700', '--group=ocf',
            '--owner=' + user, home],
        stdout=sys.stderr)

    for name in ['bashrc', 'bash_profile', 'bash_logout']:
        path = os.path.join(os.path.dirname(__file__), 'rc', name)
        subprocess.check_call(
            ['sudo', 'install', '--mode=0600', '--group=ocf',
                '--owner=' + user, path, os.path.join(home, '.' + name)],
            stdout=sys.stderr)


# TODO: is there a reason we make the user use makehttp, or should we just make
# the public_html symlink at account creation?
def create_web_dir(user):
    """Create web directory for user with appropriate permissions. We start web
    directories at 000; the user can later use makehttp to chmod them to
    something readable by the webserver if they desire."""

    path = utils.web_dir(user)
    subprocess.check_call(
        ['sudo', 'install', '-d', '--mode=0000', '--group=ocf',
            '--owner=' + user, path],
        stdout=sys.stderr)


def send_created_mail(email, realname, username):
    body = """Greetings from the Grotto of Hearst Gym,

Your OCF account has been created and is ready for use! Welcome aboard!

Your account name is: {username}

As a brand-new OCF member, you're welcome to use any and all of our services.
You can find out more about them on our wiki:

https://ocf.io/wiki

Keep in mind not to share your shiny new password with anyone, including OCF
staffers. You can always reset it online:

https://ocf.io/password

Finally, we would like to remind you that the OCF is run entirely by student
volunteers, and as such, we are always looking for new staff. If you value the
services that the OCF provides to the UC Berkeley community and want to assist
us in continuing to offer them, please visit:

https://hello.ocf.berkeley.edu/

If you have any other questions or problems, feel free to contact us by
replying to this message.

{signature}""".format(username=username,
                      signature=constants.MAIL_SIGNATURE)

    mail.send_mail(email, "[OCF] Your account has been created!", body)


def send_rejected_mail(email, realname, username, reason):
    body = """Greetings from the Grotto of Hearst Gym,

Your OCF account, {username} has been rejected for the following reason:

{reason}

For information about account eligibility, see:

https://wiki.ocf.berkeley.edu/membership/

If you have any other questions or problems, feel free to contact us by
replying to this message.

{signature}""".format(username=username,
                      reason=reason,
                      signature=constants.MAIL_SIGNATURE)

    mail.send_mail(email, "[OCF] Your account request has been rejected", body)


class ValidationWarning(ValueError):
    """Warning exception raised by validators when a staff member needs to
    manually approve an account."""
    pass


class ValidationError(ValueError):
    """Error exception raised by validators when a request should be
    rejected."""
    pass


def validate_calnet_uid(uid):
    """Verifies whether a given CalNet UID is eligible for a new OCF account.

    Checks that:
      - User doesn't already have an OCF account
      - Affiliate type is eligible"""

    # check for existing OCF accounts
    existing_accounts = search.users_by_calnet_uid(uid)

    if existing_accounts:
        raise ValidationError(
            "Calnet UID already has account: " + str(existing_accounts))

    attrs = search.user_attrs_ucb(uid)

    if not attrs:
        raise ValidationError("CalNet UID can't be found in university LDAP.")

    # check if user is eligible for an account
    affiliations = attrs['berkeleyEduAffiliations']
    if not eligible_for_account(affiliations):
        raise ValidationError(
            "Affiliate type not eligible for account: " + str(affiliations))


def eligible_for_account(affiliations):
    """Returns whether the list of affiliations makes one eligible for an
    account."""

    ALLOWED_AFFILIATES = [
        'AFFILIATE-TYPE-CONSULTANT',
        'AFFILIATE-TYPE-LBLOP STAFF',
        'AFFILIATE-TYPE-VISITING SCHOLAR',
        'AFFILIATE-TYPE-VOLUNTEER',
        'AFFILIATE-TYPE-HHMI RESEARCHER',
        'AFFILIATE-TYPE-VISITING STU RESEARCHER',
        'AFFILIATE-TYPE-LBL/DOE POSTDOC',
        'AFFILIATE-TYPE-TEMP AGENCY',
        'AFFILIATE-TYPE-COMMITTEE MEMBER',
        'AFFILIATE-TYPE-STAFF OF UC/OP/AFFILIATED ORGS',
        'AFFILIATE-TYPE-CONTRACTOR',
        'AFFILIATE-TYPE-CONCURR ENROLL']

    if any(affiliation in ALLOWED_AFFILIATES for affiliation in affiliations) \
            and 'AFFILIATE-STATUS-EXPIRED' not in affiliations:
        return True

    if ('EMPLOYEE-TYPE-ACADEMIC' in affiliations
            or 'EMPLOYEE-TYPE-STAFF' in affiliations) \
            and 'EMPLOYEE-STATUS-EXPIRED' not in affiliations:
        return True

    if 'STUDENT-TYPE-REGISTERED' in affiliations and \
            'STUDENT-STATUS-EXPIRED' not in affiliations:
        return True

    return False


def validate_username(username, realname):
    """Validates a username and realname pair to ensure:

    * Username isn't already in use
    * Username is based on realname
    * Username isn't restricted."""

    if search.user_exists(username):
        raise ValidationError("Username {} already exists.".format(username))

    try:
        validators.validate_username(username)
    except ValueError as ex:
        raise ValidationError(str(ex))

    SIMILARITY_THRESHOLD = 1

    if similarity_heuristic(realname, username) > SIMILARITY_THRESHOLD:
        raise ValidationWarning(
            "Username {} not based on real name {}".format(username, realname))

    if any(word in username for word in constants.BAD_WORDS):
        raise ValidationWarning("Username {} contains bad words")

    if any(word in username for word in constants.RESRICTED_WORDS):
        raise ValidationWarning("Username {} contains restricted words")


def similarity_heuristic(realname, username):
    """
    Return a count of the edits that turn realname into username.

    Count the number of replacements and insertions (*ignoring* deletions) for
    the minimum number of edits (*including* deletions) that turn any of the
    permutations of words orderings or initialisms of realname into username,
    using the built-in difflib.SequenceMatcher class. SequenceMatcher finds the
    longest continguous matching subsequence and continues this process
    recursively.

    This is usually the edit distance with zero deletion cost, but is
    intentionally greater for longer realnames with short matching
    subsequences, which are likely coincidental.

    For most usernames based on real names, this number is 0."""

    # The more words in realname, the more permutations. O(n!) is terrible!
    max_words = 8
    max_iterations = math.factorial(max_words)

    words = re.findall("\w+", realname)
    initials = [word[0] for word in words]

    if len(words) > max_words:
        print("Not trying all permutations of '{}' for similarity.".format(
              realname))

    distances = []
    for sequence in [words, initials]:
        for i, permutation in enumerate(itertools.permutations(sequence)):
            if i > max_iterations:
                break
            s = "".join(permutation).lower()
            matcher = difflib.SequenceMatcher(None, s, username)
            edits = matcher.get_opcodes()
            distance = sum(edit[4] - edit[3]
                           for edit in edits
                           if edit[0] in ["replace", "insert"])
            if distance == 0:
                # Edit distance cannot be smaller than 0, so return early.
                return 0
            distances.append(distance)
    return min(distances)
