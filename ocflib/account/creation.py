import difflib
import itertools
import math
import os.path
import re
import subprocess
from collections import namedtuple
from contextlib import contextmanager
from grp import getgrnam

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

import ocflib.account.search as search
import ocflib.account.utils as utils
import ocflib.account.validators as validators
import ocflib.constants as constants
from ocflib.infra.kerberos import create_kerberos_principal_with_keytab
from ocflib.infra.ldap import create_ldap_entry_with_keytab
from ocflib.infra.ldap import ldap_ocf
from ocflib.misc.mail import send_mail
from ocflib.misc.mail import send_problem_report
from ocflib.misc.validators import valid_email


def create_account(request, creds, report_status):
    """Create an account as idempotently as possible."""  # TODO: docstring

    # TODO: check if kerberos principal already exists; skip this if so
    with report_status('Creating', 'Created', 'Kerberos keytab'):
        create_kerberos_principal_with_keytab(
            request.user_name,
            creds.kerberos_keytab,
            creds.kerberos_principal,
            password=decrypt_password(
                request.encrypted_password,
                creds.encryption_key,
            ),
        )

    # TODO: check if LDAP entry already exists; skip this if so
    with report_status('Finding', 'Found', 'first available UID'):
        new_uid = _get_first_available_uid()

    dn = 'uid={user},{base_people}'.format(
        user=request.user_name,
        base_people=constants.OCF_LDAP_PEOPLE,
    )
    attrs = {
        'objectClass': ['ocfAccount', 'account', 'posixAccount'],
        'cn': [request.real_name],
        'uidNumber': [str(new_uid)],
        'gidNumber': [str(getgrnam('ocf').gr_gid)],
        'homeDirectory': [utils.home_dir(request.user_name)],
        'loginShell': ['/bin/bash'],
        'mail': [request.email],
        'userPassword': ['{SASL}' + request.user_name + '@OCF.BERKELEY.EDU'],
    }
    if request.calnet_uid:
        attrs['calnetUid'] = [str(request.calnet_uid)]
    else:
        attrs['callinkOid'] = [str(request.callink_oid)]

    with report_status('Creating', 'Created', 'LDAP entry'):
        create_ldap_entry_with_keytab(
            dn, attrs, creds.kerberos_keytab, creds.kerberos_principal,
        )

    with report_status('Creating', 'Created', 'home and web directories'):
        create_home_dir(request.user_name)
        create_web_dir(request.user_name)

    send_created_mail(request)
    # TODO: logging to syslog, files


def _get_first_available_uid():
    """Return the first available UID number.

    Searches our entire People ou in order to find it. It seems like there
    should be a better way to do this, but quick searches don't show any.

    We hard-code a value we know has already been reached and only select
    entries greater than that for performance. We then use a module-level
    dict to cache our output for the next function call.
    """
    min_uid = _cache['known_uid']
    with ldap_ocf() as c:
        c.search(
            constants.OCF_LDAP_PEOPLE,
            '(uidNumber>={KNOWN_MIN})'.format(KNOWN_MIN=min_uid),
            attributes=['uidNumber'],
        )
        uids = [int(entry['attributes']['uidNumber'][0]) for entry in c.response]
        if len(uids) > 2500:
            send_problem_report((
                'Found {} accounts with UID >= {}, '
                'you should bump the constant for speed.'
            ).format(len(uids), min_uid))
        if uids:
            max_uid = max(uids)
            _cache['known_uid'] = max_uid
        else:
            # If cached UID is later deleted, LDAP response will be empty.
            max_uid = min_uid
        return max_uid + 1


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


def create_web_dir(user):
    """Create web directory for user with appropriate permissions.

    All users are given a working web directory and public_html symlink at
    account creation. They can later use `makehttp` to fix these if they bork
    the permissions or symlink.
    """
    path = utils.web_dir(user)

    # create web directory
    subprocess.check_call([
        'sudo', 'install',
        '-d', '--mode=0755', '--group=ocf', '--owner=' + user,
        '--',
        path,
    ])

    # symlink it from ~user/public_html
    subprocess.check_call([
        'sudo', '-u', user,
        'ln', '-fs', '--', path, os.path.join(utils.home_dir(user), 'public_html'),
    ])


def send_created_mail(request):
    body = """Greetings from the Grotto of Hearst Gym,

Your OCF account has been created and is ready for use! Welcome aboard!

Your account name is: {request.user_name}

As a brand-new OCF member, you're welcome to use any and all of our services.
Some key highlights:

    - Access to our swanky computer lab (6A Hearst Gym)
    - 250 pages of free printing per semester
    - Web hosting: https://www.ocf.berkeley.edu/~{request.user_name}/

You can find out the cool things you can do on our wiki:
https://ocf.io/wiki

Keep in mind not to share your shiny new password with anyone, including OCF
staffers. You can always reset it online:

https://ocf.io/password

Finally, we'd like to remind you that the OCF is run completely by student
volunteers (people like you)! If you value the services we provide, check us
out and consider getting involved!

https://hello.ocf.berkeley.edu/

If you have any other questions, feel free to reply to this message!

{signature}""".format(request=request,
                      signature=constants.MAIL_SIGNATURE)

    send_mail(request.email, '[OCF] Your account has been created!', body)


def send_rejected_mail(request, reason):
    body = """Greetings from the Grotto of Hearst Gym,

Your OCF account, {request.user_name} has been rejected for the following reason:

{reason}

For information about account eligibility, see:

https://wiki.ocf.berkeley.edu/membership/

If you have any other questions or problems, feel free to contact us by
replying to this message.

{signature}""".format(request=request,
                      reason=reason,
                      signature=constants.MAIL_SIGNATURE)

    send_mail(
        request.email, '[OCF] Your account request has been rejected', body)


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
        raise ValidationWarning('Username {} contains bad words'.format(username))

    if any(word in username for word in constants.RESTRICTED_WORDS):
        raise ValidationWarning('Username {} contains restricted words'.format(username))


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


def validate_request(request, credentials, session):
    """Validate a request, returning lists of errors and warnings."""
    from ocflib.account.submission import username_pending
    from ocflib.account.submission import user_has_request_pending

    errors, warnings = [], []

    @contextmanager
    def validate_section():
        try:
            yield
        except ValidationWarning as ex:
            warnings.append(str(ex))
        except ValidationError as ex:
            errors.append(str(ex))

    # TODO: figure out where to sanitize real_name

    # user name
    with validate_section():
        if username_pending(session, request):
            raise ValidationError('Username {} has already been requested.'.format(
                request.user_name,
            ))

        validate_username(request.user_name, request.real_name)

    # calnet uid / callink oid
    with validate_section():
        if request.is_group:
            validate_callink_oid(request.callink_oid)
        else:
            validate_calnet_uid(request.calnet_uid)

        if user_has_request_pending(session, request):
            raise ValidationError('You have already requested an account.')

    # email
    with validate_section():
        validate_email(request.email)

    # password
    with validate_section():
        password = decrypt_password(
            request.encrypted_password,
            credentials.encryption_key,
        )
        validate_password(request.user_name, password)

    return errors, warnings


class NewAccountRequest(namedtuple('NewAccountRequest', [
    'user_name',
    'real_name',
    'is_group',
    'calnet_uid',
    'callink_oid',
    'email',
    'encrypted_password',
    'handle_warnings',
])):
    """Request for account creation.

    :param user_name:
    :param real_name:
    :param is_group:
    :param calnet_uid: uid (or None)
    :param callink_oid: oid (or None)
    :param email:
    :param encrypted_password:
    :param handle_warnings: one of WARNINGS_WARN, WARNINGS_SUBMIT,
                            WARNINGS_CREATE
        WARNINGS_WARN: don't create account, return warnings
        WARNINGS_SUBMIT: don't create account, submit for staff approval
        WARNINGS_CREATE: create the account anyway
    """
    WARNINGS_WARN = 'warn'
    WARNINGS_SUBMIT = 'submit'
    WARNINGS_CREATE = 'create'

    def to_dict(self):
        return {
            field: getattr(self, field)
            for field in self._fields if field != 'encrypted_password'
        }


# We use a module-level dict to "cache" across function calls.
_cache = {'known_uid': 35000}
_get_first_available_uid()
