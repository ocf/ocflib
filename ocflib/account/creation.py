import difflib
import itertools
import math
import os.path
import re
import subprocess
from grp import getgrnam

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

import ocflib.account.search as search
import ocflib.account.utils as utils
import ocflib.account.validators as validators
import ocflib.constants as constants
import ocflib.misc.mail as mail
from ocflib.infra.kerberos import create_kerberos_principal_with_keytab
from ocflib.infra.ldap import create_ldap_entry_with_keytab
from ocflib.infra.ldap import ldap_ocf
from ocflib.misc.validators import valid_email


def create_account(
    user,
    password,
    real_name,
    email,
    calnet_uid,
    callink_oid,
    keytab,
    admin_principal,
):
    """Create an account as idempotently as possible."""  # TODO: docstring
    new_uid = _get_first_available_uid()

    # TODO: check if kerberos principal already exists; skip this if so
    create_kerberos_principal_with_keytab(
        user,
        keytab,
        admin_principal,
        password=password,
    )

    # TODO: check if LDAP entry already exists; skip this if so
    dn = 'uid={user},{base_people}'.format(
        user=user,
        base_people=constants.OCF_LDAP_PEOPLE,
    )
    sasl_fake_password = '{SASL}' + user + '@OCF.BERKELEY.EDU'
    attrs = {
        'objectClass': ['ocfAccount', 'account', 'posixAccount'],
        'cn': [real_name],
        'uidNumber': [str(new_uid)],
        'gidNumber': [str(getgrnam('ocf').gr_gid)],
        'homeDirectory': [utils.home_dir(user)],
        'loginShell': ['/bin/bash'],
        'mail': [email],
        'userPassword': [sasl_fake_password],
    }

    if calnet_uid:
        attrs['calnetUid'] = [str(calnet_uid)]

    if callink_oid:
        attrs['callinkOid'] = [str(callink_oid)]

    create_ldap_entry_with_keytab(dn, attrs, keytab, admin_principal)

    create_home_dir(user)
    create_web_dir(user)

    # TODO: send email to new user
    # TODO: logging to syslog, files, and IRC


def _get_first_available_uid():
    """Returns the first available UID number.

    Searches our entire People ou in order to find it. It seems like there
    should be a better way to do this, but quick searches don't show any.
    """
    with ldap_ocf() as c:
        c.search(
            constants.OCF_LDAP_PEOPLE,
            '(uidNumber=*)',
            attributes=['uidNumber'],
        )
        return max(int(entry['attributes']['uidNumber'][0])
                   for entry in c.response) + 1


def create_home_dir(user):
    """Create home directory for user. Makes a directory with appropriate
    permissions, then copies in OCF's skeleton dotfiles.
    """
    home = utils.home_dir(user)
    subprocess.check_call(
        ['sudo', 'install', '-d', '--mode=0700', '--group=ocf',
            '--owner=' + user, home])

    for name in ['bashrc', 'bash_profile', 'bash_logout']:
        path = os.path.join(os.path.dirname(__file__), 'rc', name)
        subprocess.check_call(
            ['sudo', 'install', '--mode=0600', '--group=ocf',
                '--owner=' + user, path, os.path.join(home, '.' + name)])


# TODO: is there a reason we make the user use makehttp, or should we just make
# the public_html symlink at account creation?
def create_web_dir(user):
    """Create web directory for user with appropriate permissions. We start web
    directories at 000; the user can later use makehttp to chmod them to
    something readable by the webserver if they desire.
    """
    path = utils.web_dir(user)
    subprocess.check_call(
        ['sudo', 'install', '-d', '--mode=0000', '--group=ocf',
            '--owner=' + user, path])


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

    mail.send_mail(email, '[OCF] Your account has been created!', body)


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

    mail.send_mail(email, '[OCF] Your account request has been rejected', body)


class ValidationWarning(ValueError):
    """Warning exception raised by validators when a staff member needs to
    manually approve an account."""
    pass


class ValidationError(ValueError):
    """Error exception raised by validators when a request should be
    rejected."""
    pass


def validate_callink_oid(oid):
    """Verifies whether a given CalLink OID is eligible for a new OCF account.

    Checks that:
      - User doesn't already have an OCF account
        Issues a warning which staff can override if they do (unlike
        validate_calnet_uid, which issues an error).

    OID `0` can create an infinite number of accounts; we use this for
    department-sponsored groups and others without CalLink OIDs.
    """

    if oid == 0:
        return

    # check for existing OCF accounts
    existing_accounts = search.users_by_callink_oid(oid)

    if existing_accounts:
        raise ValidationWarning(
            'CalLink OID already has account: ' + str(existing_accounts))

    # TODO: verify CalLink OID exists, once we've written some basic CalLink
    # support into ocflib


def validate_calnet_uid(uid):
    """Verifies whether a given CalNet UID is eligible for a new OCF account.

    Checks that:
      - User doesn't already have an OCF account
      - Affiliate type is eligible"""

    # check for existing OCF accounts
    existing_accounts = search.users_by_calnet_uid(uid)

    if existing_accounts:
        raise ValidationError(
            'CalNet UID already has account: ' + str(existing_accounts))

    attrs = search.user_attrs_ucb(uid)

    if not attrs:
        raise ValidationError("CalNet UID can't be found in university LDAP.")

    # check if user is eligible for an account
    affiliations = attrs['berkeleyEduAffiliations']
    if not eligible_for_account(affiliations):
        raise ValidationWarning(
            'Affiliate type not eligible for account: ' + str(affiliations))


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
        raise ValidationError('Username {} already exists.'.format(username))

    try:
        validators.validate_username(username)
    except ValueError as ex:
        raise ValidationError(str(ex))

    SIMILARITY_THRESHOLD = 1

    if similarity_heuristic(realname, username) > SIMILARITY_THRESHOLD:
        raise ValidationWarning(
            'Username {} not based on real name {}'.format(username, realname))

    if any(word in username for word in constants.BAD_WORDS):
        raise ValidationWarning('Username {} contains bad words')

    if any(word in username for word in constants.RESTRICTED_WORDS):
        raise ValidationWarning('Username {} contains restricted words')


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

    words = re.findall('\w+', realname)
    initials = [word[0] for word in words]

    if len(words) > max_words:
        print("Not trying all permutations of '{}' for similarity.".format(
              realname))

    distances = []
    for sequence in [words, initials]:
        for i, permutation in enumerate(itertools.permutations(sequence)):
            if i > max_iterations:
                break
            s = ''.join(permutation).lower()
            matcher = difflib.SequenceMatcher(None, s, username)
            edits = matcher.get_opcodes()
            distance = sum(edit[4] - edit[3]
                           for edit in edits
                           if edit[0] in ['replace', 'insert'])
            if distance == 0:
                # Edit distance cannot be smaller than 0, so return early.
                return 0
            distances.append(distance)
    return min(distances)


def validate_email(email):
    if not valid_email(email):
        raise ValidationError('Invalid email.')


def validate_password(username, password):
    try:
        validators.validate_password(username, password)
    except ValueError as ex:
        raise ValidationError(str(ex))


def encrypt_password(password, pubkey_path):
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
    key = RSA.importKey(open(pubkey_path).read())
    RSA_CIPHER = PKCS1_OAEP.new(key)
    return RSA_CIPHER.encrypt(password.encode('ascii'))


def decrypt_password(password, privkey_path):
    """Decrypts a user password."""
    key = RSA.importKey(open(privkey_path).read())
    RSA_CIPHER = PKCS1_OAEP.new(key)
    return RSA_CIPHER.decrypt(password).decode('ascii')
