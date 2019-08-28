import difflib
import itertools
import math
import os
import re
import subprocess
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from grp import getgrnam
from subprocess import call

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

import ocflib.account.search as search
import ocflib.account.utils as utils
import ocflib.account.validators as validators
from ocflib.infra.kerberos import create_kerberos_principal_with_keytab
from ocflib.infra.kerberos import get_kerberos_principal_with_keytab
from ocflib.infra.ldap import create_ldap_entry
from ocflib.infra.ldap import ldap_ocf
from ocflib.infra.ldap import OCF_LDAP_PEOPLE
from ocflib.misc.mail import jinja_mail_env
from ocflib.misc.mail import send_mail
from ocflib.misc.validators import valid_email
from ocflib.printing.quota import SEMESTERLY_QUOTA


_KNOWN_UID = 71136
BAD_WORDS = frozenset((
    'anal', 'anus', 'arse', 'ass', 'bastard', 'bitch', 'biatch', 'bloody', 'blowjob', 'bollock',
    'bollok', 'boner', 'chink', 'clit', 'cock', 'coon', 'cunt', 'damn', 'dick', 'dildo', 'douche',
    'dyke', 'fag', 'fellate', 'fellatio', 'felching', 'fuck', 'flange', 'hell', 'homo', 'jerk', 'jizz', 'kike',
    'labia', 'muff', 'nigger', 'nigga', 'penis', 'piss', 'prick', 'pube', 'pussy', 'queer', 'scrotum',
    'sex', 'shit', 'slut', 'smegma', 'terrorist', 'twat', 'vagina', 'wank', 'whore'
))
RESTRICTED_WORDS = frozenset(('ocf', 'ucb', 'berkeley', 'university'))

CREATE_PUBLIC_KEY = '''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3xG2dczz2y+qc0AgTZ1L
Jrun4RbcMf7z7AFqPqIQrtbuJprg6EQPHd2EDjMt9rJm929tTatjLu7TcNisq9lW
AMU85c1nM6l4ce58mIXGzaB5yCGP0Qfcos5o00xJOmRVmxZGB5D2Jli+JbmEHPpo
KbvI3DuNLNbS+MxXawudEDVj0xA86Iv8biHqq//xMD+SicOzN4ZrjKarT9MdQYL+
JDNjiYba1ZiNLiqXeLGS2IVYAd88etX+V5gxAvl0bGHzgeHodutxUf46QCg7cmvm
5lQsbiYUABiEsE1OejSEfb+7mtuhxu+MeVXCYr341axa0IHorj4qURxKOi/CTn5f
zwIDAQAB
-----END PUBLIC KEY-----'''

# Inclusive endpoints
RESERVED_UID_RANGES = [
    # 61184-65519 are the systemd dymanic users
    # 65534 is the nobody user
    # 65535 is the invalid user
    # we reserve the gaps between these for extra safety
    (61184, 65535),
]


def _get_first_available_uid(known_uid=_KNOWN_UID):
    """Return the first available UID number.

    Searches our entire People ou in order to find it. It seems like there
    should be a better way to do this, but quick searches don't show any.

    We hard-code a value we know has already been reached and only select
    entries greater than that for performance. This value can then be cached
    and passed back in to make subsequent calls faster.
    """
    with ldap_ocf() as c:
        c.search(
            OCF_LDAP_PEOPLE,
            '(uidNumber>={KNOWN_MIN})'.format(KNOWN_MIN=known_uid),
            attributes=['uidNumber'],
        )
        uids = [int(entry['attributes']['uidNumber']) for entry in c.response]
    if uids:
        max_uid = max(uids)
    else:
        # If cached UID is later deleted, LDAP response will be empty.
        max_uid = known_uid

    assert all(start <= end for start, end in RESERVED_UID_RANGES)
    next_uid = max_uid + 1
    for start, end in sorted(RESERVED_UID_RANGES):
        if start <= next_uid <= end:
            next_uid = end + 1

    return next_uid


def create_account(request, creds, report_status, known_uid=_KNOWN_UID):
    """Create an account as idempotently as possible.

    :param known_uid: where to start searching for unused UIDs (see
        _get_first_available_uid)
    :return: the UID of the newly created account
    """
    # TODO: better docstring

    if get_kerberos_principal_with_keytab(
        request.user_name,
        creds.kerberos_keytab,
        creds.kerberos_principal,
    ):
        report_status('kerberos principal already exists; skipping creation')
    else:
        with report_status('Creating', 'Created', 'Kerberos keytab'):
            create_kerberos_principal_with_keytab(
                request.user_name,
                creds.kerberos_keytab,
                creds.kerberos_principal,
                password=decrypt_password(
                    request.encrypted_password,
                    RSA.importKey(open(creds.encryption_key).read()),
                ),
            )

    if search.user_attrs(request.user_name):
        report_status('LDAP entry already exists; skipping creation')
    else:
        with report_status('Finding', 'Found', 'first available UID'):
            new_uid = _get_first_available_uid(known_uid)

        dn = utils.dn_for_username(request.user_name)
        attrs = {
            'objectClass': ['ocfAccount', 'account', 'posixAccount'],
            'cn': [request.real_name],
            'uidNumber': new_uid,
            'gidNumber': getgrnam('ocf').gr_gid,
            'homeDirectory': utils.home_dir(request.user_name),
            'loginShell': '/bin/bash',
            'ocfEmail': request.user_name + '@ocf.berkeley.edu',
            'mail': [request.email],
            'userPassword': '{SASL}' + request.user_name + '@OCF.BERKELEY.EDU',
            'creationTime': datetime.now(timezone.utc).astimezone(),
        }
        if request.calnet_uid:
            attrs['calnetUid'] = request.calnet_uid
        else:
            attrs['callinkOid'] = request.callink_oid

        with report_status('Creating', 'Created', 'LDAP entry'):
            create_ldap_entry(
                dn,
                attrs,
                keytab=creds.kerberos_keytab,
                admin_principal=creds.kerberos_principal,
            )

            # invalidate passwd cache so that we can immediately chown files
            # XXX: sometimes this fails, but that's okay because it means
            # nscd isn't running anyway
            call(('sudo', 'nscd', '-i', 'passwd'))

    with report_status('Creating', 'Created', 'home and web directories'):
        create_home_dir(request.user_name)
        ensure_web_dir(request.user_name)

    send_created_mail(request)
    # TODO: logging to syslog, files

    return new_uid


def create_home_dir(user):
    """Create home directory for user with appropriate permissions."""
    home = utils.home_dir(user)
    subprocess.check_call(
        ['sudo', 'install', '-d', '--mode=0700', '--group=ocf',
            '--owner=' + user, home])


def ensure_web_dir(user):
    """Ensure user has web directory with appropriate permissions and
    public_html symlink.

    All users are given a working web directory and public_html symlink at
    account creation. They can later use `makehttp` to fix these if they bork
    the permissions or symlink. If there is already a file in the user's home
    folder named 'public_html', it will be renamed by appending a timestamp.
    """
    path = utils.web_dir(user)

    # ensure web directory exists and has the right permissiosn
    subprocess.check_call([
        'sudo', 'install',
        '-d', '--mode=0755', '--group=ocf', '--owner=' + user,
        '--',
        path,
    ])

    public_html_path = utils.public_html_path(user)

    # rename any existing files named ~user/public_html
    if os.path.exists(public_html_path) and os.path.realpath(public_html_path) != path:
        timestamp = datetime.now().strftime('%m%d%Y-%H%M%S')
        subprocess.check_call([
            'sudo', 'mv', public_html_path, public_html_path + '.' + timestamp,
        ])

    # symlink web dir from ~user/public_html
    subprocess.check_call([
        'sudo', '-u', user,
        'ln', '-fs', '--', path, public_html_path,
    ])


def send_created_mail(request):
    body = jinja_mail_env.get_template(
        'account/mail_templates/account-created.jinja',
    ).render(
        request=request,
        semesterly_quota=SEMESTERLY_QUOTA,
    )
    send_mail(request.email, '[OCF] Your account has been created!', body)


def send_rejected_mail(request, reason):
    body = jinja_mail_env.get_template(
        'account/mail_templates/account-rejected.jinja',
    ).render(request=request, reason=reason)
    send_mail(request.email, '[OCF] Your account request has been rejected', body)


class ValidationWarning(Exception):
    """Warning exception raised by validators when a staff member needs to
    manually approve an account."""


class ValidationError(Exception):
    """Error exception raised by validators when a request should be
    rejected."""


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

    # TODO: Uncomment when we get privileged LDAP bind.
    # check if user is eligible for an account
    # affiliations = attrs['berkeleyEduAffiliations']
    # if not eligible_for_account(affiliations):
    #    raise ValidationWarning(
    #        'Affiliate type not eligible for account: ' + str(affiliations))


def eligible_for_account(affiliations):
    """Returns whether the list of affiliations makes one eligible for an
    account.
    """
    affiliations = set(affiliations)
    ALLOWED_AFFILIATES = {
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
        'AFFILIATE-TYPE-CONCURR ENROLL',
    }

    if (
            affiliations & ALLOWED_AFFILIATES and
            'AFFILIATE-STATUS-EXPIRED' not in affiliations
    ):
        return True

    if (
            {'EMPLOYEE-TYPE-ACADEMIC', 'EMPLOYEE-TYPE-STAFF'} & affiliations and
            'EMPLOYEE-STATUS-EXPIRED' not in affiliations
    ):
        return True

    # It seems that "NOT REGISTERED" students indicates students who have
    # registration blocks or who haven't paid their university fees.
    #
    # BoD voted to allow these members to create accounts because in most cases
    # they are still students and will eventually become registered. See
    # rt#4282 for more details.
    if (
            {'STUDENT-TYPE-REGISTERED', 'STUDENT-TYPE-NOT REGISTERED'} & affiliations and
            'STUDENT-STATUS-EXPIRED' not in affiliations
    ):
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

    SIMILARITY_THRESHOLD = 2

    if similarity_heuristic(realname, username) > SIMILARITY_THRESHOLD:
        raise ValidationWarning(
            'Username {} not based on real name {}.'.format(username, realname))

    if any(word in username for word in BAD_WORDS):
        raise ValidationWarning('Username {} contains bad words.'.format(username))

    if any(word in username for word in RESTRICTED_WORDS):
        raise ValidationWarning('Username {} contains restricted words.'.format(username))


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

    words = re.findall(r'\w+', realname)
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


def encrypt_password(password, pubkey):
    """Encrypts (not hashes) a user password to be stored on disk while it
    awaits approval.

    Generate the public / private keys with the following code:
    >>> from Crypto.PublicKey import RSA
    >>> key = RSA.generate(2048)
    >>> open("private.pem", "w").write(key.exportKey())
    >>> open("public.pem", "w").write(key.publickey().exportKey())
    """
    RSA_CIPHER = PKCS1_OAEP.new(pubkey)
    return RSA_CIPHER.encrypt(password.encode('ascii'))


def decrypt_password(password, privkey):
    """Decrypts a user password."""
    RSA_CIPHER = PKCS1_OAEP.new(privkey)
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
            RSA.importKey(open(credentials.encryption_key).read()),
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
