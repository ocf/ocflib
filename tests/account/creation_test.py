from contextlib import contextmanager
from textwrap import dedent

import mock
import pytest
from Crypto.PublicKey import RSA
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import ocflib.constants as constants
from ocflib.account.creation import _get_first_available_uid
from ocflib.account.creation import _KNOWN_UID
from ocflib.account.creation import create_account
from ocflib.account.creation import create_home_dir
from ocflib.account.creation import create_web_dir
from ocflib.account.creation import decrypt_password
from ocflib.account.creation import eligible_for_account
from ocflib.account.creation import encrypt_password
from ocflib.account.creation import NewAccountRequest
from ocflib.account.creation import send_created_mail
from ocflib.account.creation import send_rejected_mail
from ocflib.account.creation import validate_callink_oid
from ocflib.account.creation import validate_calnet_uid
from ocflib.account.creation import validate_email
from ocflib.account.creation import validate_password
from ocflib.account.creation import validate_request
from ocflib.account.creation import validate_username
from ocflib.account.creation import ValidationError
from ocflib.account.creation import ValidationWarning
from ocflib.account.submission import AccountCreationCredentials
from ocflib.account.submission import Base
from ocflib.infra.ldap import ldap_ocf

WEAK_KEY = dedent(
    """\
    -----BEGIN RSA PRIVATE KEY-----
    MIICWwIBAAKBgQDGkGNFk/yy8HphSvvsmCpMF1vGbJeZXw2AmlLfTLcGJkZuvelu
    qJTGepGjeEeML6GrE03dI330mWtnC8jdhmwaELndqoPQ3Ks1eXF5usvDeYoRVir0
    ekqJtd2+7eBQ4xrRIA5YohoE31VGQ7ZaQ0GLMuWjldTe3bx+5OJqB0pE5QIDAQAB
    AoGAZtTX1GyzbagEeOZwWTLklMt0B+qtCAyl3XgOev4rus+PokJP5bMAeVl4mwPr
    aboxK3uv01pSHJ5ndNIxkCfRSzSuKvddfoaDrP97dbS0boqHyJmG38U2kxaMufBP
    rFP4a05TajdU9/rQSaGGmTkgDmRfJId5aDfJh6ToKMEYnQECQQDYb0Nj9mAWz5ja
    btXyegMespiK1UnyrZlRKsm0zcnEZ4NBE/lgMiJJXkfhdS5af9ORPmDjlQfwuHtZ
    N5mEKXNRAkEA6tzQPWCIL3gz0FYVX+l00JTFRIFA1yfvHiF4XjNZUr1TjXdGhto5
    DqV39XTk1CPtXNJto9AmNLf8zJD5xsqLVQJAToXnfD/p0rzUpwMpSgSsVxnSsCP7
    5TjIdCNC9P7oYgJwI0883YKy38195LVf8OOJfZuVCVyLefFkhxTd9I4ZUQJAO0ft
    D/DzrveqLGXuEz18DMHgYQA2+5fK1VIhbbWMUEQVeNmoZZVjXX0KoFwW/izrVsiO
    gBCj9B6UopXdVf392QJAcCUgxV6Ca6iWplAKHsaJ7sG+aQOaYI8m3d3MqJ5g34GB
    CqXzvT0v5ZrGj+K9dWDb+pYvGWhc2iU/e40yyj0G9w==
    -----END RSA PRIVATE KEY-----"""
)


@pytest.fixture
def session(fake_credentials):
    engine = create_engine(fake_credentials.mysql_uri)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.yield_fixture
def fake_new_account_request(mock_rsa_key):
    yield NewAccountRequest(
        user_name='someuser',
        real_name='Some User',
        is_group=False,
        calnet_uid=123456,
        callink_oid=None,
        email='some.user@ocf.berkeley.edu',
        encrypted_password=encrypt_password('hunter2000', RSA.importKey(WEAK_KEY)),
        handle_warnings=NewAccountRequest.WARNINGS_WARN,
    )


@pytest.yield_fixture
def mock_rsa_key(tmpdir):
    test_key = tmpdir.join('test.key')
    test_key.write((WEAK_KEY + '\n').encode('ascii'))
    yield test_key.strpath
    test_key.remove()


class TestFirstAvailableUID:

    def test_first_uid(self):
        connection = mock.Mock(response=[
            {'attributes': {'uidNumber': [999000]}},
            {'attributes': {'uidNumber': [999200]}},
            {'attributes': {'uidNumber': [999100]}},
        ])

        @contextmanager
        def ldap_ocf():
            yield connection

        with mock.patch('ocflib.account.creation.ldap_ocf', ldap_ocf):
            next_uid = _get_first_available_uid()

        assert next_uid == 999201

    def test_max_uid_constant_not_too_small(self):
        """Test that the _KNOWN_UID constant is sufficiently large.

        The way we find the next available UID is very slow because there is no
        way to do a query like "find the max UID from all users" in LDAP.
        We instead have to find all users and take the max ourselves. This can
        take ~15 seconds.

        By hardcoding a known min, we just select accounts with uid >
        _KNOWN_UID, which is much faster. This makes finding available UIDs
        faster the first time a query is made. The result can be cached to make
        subsequent attempts even faster.
        """
        with ldap_ocf() as c:
            c.search(
                constants.OCF_LDAP_PEOPLE,
                '(uidNumber>={KNOWN_MIN})'.format(KNOWN_MIN=_KNOWN_UID),
                attributes=['uidNumber'],
            )
            num_uids = len(c.response)

        if num_uids > 2500:
            raise AssertionError((
                'Found {} accounts with UID >= {}, you should bump the constant for speed.'
            ).format(num_uids, _KNOWN_UID))


class TestCreateDirectories:

    @mock.patch('subprocess.check_call')
    def test_create_home_dir(self, check_call):
        create_home_dir('ckuehl')

        calls = [mock.call(
            ['sudo', 'install', '-d', '--mode=0700', '--group=ocf',
                '--owner=ckuehl', '/home/c/ck/ckuehl'],
        )]

        check_call.assert_has_calls(calls)

    @mock.patch('subprocess.check_call')
    def test_create_web_dir(self, check_call):
        create_web_dir('ckuehl')
        check_call.assert_has_calls([
            mock.call([
                'sudo', 'install', '-d', '--mode=0755', '--group=ocf', '--owner=ckuehl',
                '--', '/services/http/users/c/ckuehl',
            ]),
            mock.call([
                'sudo', '-u', 'ckuehl', 'ln', '-fs', '--',
                '/services/http/users/c/ckuehl', '/home/c/ck/ckuehl/public_html',
            ]),
        ])


class TestUsernameBasedOnRealName:

    @pytest.mark.parametrize('username,realname,success', [
        ['ckuehl', 'Christopher Kuehl', True],
        ['ckuehl', 'CHRISTOPHER B KUEHL', True],
        ['kuehl', 'CHRISTOPHER B KUEHL', True],
        ['cbk', 'CHRISTOPHER B KUEHL', True],

        ['rejectme', 'Christopher Kuehl', False],
        ['penguin', 'Christopher Kuehl', False],
        ['daradib', 'Christopher Kuehl', False],
    ])
    @mock.patch('ocflib.account.validators.validate_username')
    @mock.patch('ocflib.account.search.user_exists', return_value=False)
    def test_some_names(self, _, __, username, realname, success,):
        """Test some obviously good and bad usernames."""
        try:
            validate_username(username, realname)
        except ValidationWarning as ex:
            if success:
                pytest.fail(
                    'Received unexpected error: {error}'.format(error=ex),
                )

    @pytest.mark.parametrize('username', [
        'shitup',
        'ucbcop',
        'suxocf',
    ])
    @mock.patch('ocflib.account.search.user_exists', return_value=False)
    @mock.patch('ocflib.account.creation.similarity_heuristic', return_value=0)
    def test_warning_names(self, _, __, username):
        """Ensure that we raise warnings when bad/restricted words appear."""
        with pytest.raises(ValidationWarning):
            validate_username(username, username)

    @pytest.mark.parametrize('username', [
        'wordpress',
        'systemd',
        'ocf',
        'ocfrocks',
    ])
    @mock.patch('ocflib.account.search.user_exists', return_value=False)
    @mock.patch('ocflib.account.creation.similarity_heuristic', return_value=0)
    def test_error_names(self, _, __, username):
        """Ensure that we raise errors when appropriate."""
        with pytest.raises(ValidationError):
            validate_username(username, username)

    def test_error_user_exists(self):
        """Ensure that we raise an error if the username already exists."""
        with pytest.raises(ValidationError):
            validate_username('ckuehl', 'Chris Kuehl')

    @mock.patch('ocflib.account.validators.validate_username')
    @mock.patch('ocflib.account.search.user_exists', return_value=False)
    def test_long_names(self, _, __):
        """In the past, create has gotten "stuck" trying millions of
        combinations of real names because we try permutations of the words in
        the real name."""
        with pytest.raises(ValidationWarning):
            # 16! = 2.09227899e13, so if this works, it's definitely not
            # because we tried all possibilities
            validate_username(
                'nomatch',
                'I Have Sixteen Names A B C D E F G H I J K L',
            )


class TestAccountEligibility:

    @pytest.mark.parametrize('bad_uid', [
        1034192,     # good uid, but already has account
        9999999999,  # fake uid, not in university ldap
    ])
    def test_validate_calnet_uid_error(self, bad_uid):
        with pytest.raises(ValidationError):
            validate_calnet_uid(bad_uid)

    def test_validate_calnet_uid_success(self, mock_valid_calnet_uid):
        validate_calnet_uid(9999999999999)

    def test_validate_calnet_affiliations_failure(self, mock_invalid_calnet_uid):
        with pytest.raises(ValidationWarning):
            validate_calnet_uid(9999999999999)

    @pytest.mark.parametrize('affiliations,eligible', [
        (['AFFILIATE-TYPE-CONSULTANT'], True),
        (['AFFILIATE-TYPE-CONSULTANT', 'AFFILIATE-STATUS-EXPIRED'], False),

        (['EMPLOYEE-TYPE-ACADEMIC'], True),
        (['EMPLOYEE-TYPE-STAFF'], True),
        (['EMPLOYEE-TYPE-ACADEMIC', 'EMPLOYEE-STATUS-EXPIRED'], False),
        (['EMPLOYEE-STATUS-EXPIRED', 'AFFILIATE-TYPE-CONSULTANT'], True),
        (['EMPLOYEE-STATUS-EXPIRED', 'STUDENT-TYPE-REGISTERED'], True),

        (['STUDENT-TYPE-REGISTERED'], True),
        (['STUDENT-TYPE-NOT REGISTERED'], True),
        (['STUDENT-TYPE-REGISTERED', 'STUDENT-STATUS-EXPIRED'], False),
        (['STUDENT-TYPE-NOT REGISTERED', 'STUDENT-STATUS-EXPIRED'], False),
        (['STUDENT-STATUS-EXPIRED'], False),

        ([], False),
    ])
    def test_affiliations(self, affiliations, eligible):
        assert eligible_for_account(affiliations) == eligible


class TestSendMail:

    FREE_PRINTING_TEXT = 'pages of free printing per semester'
    VHOST_TEXT = 'virtual hosting'

    @mock.patch('ocflib.account.creation.send_mail')
    def test_send_created_mail_individual(self, send_mail, fake_new_account_request):
        fake_new_account_request = fake_new_account_request._replace(is_group=False)
        send_created_mail(fake_new_account_request)
        send_mail.assert_called_once_with(
            fake_new_account_request.email,
            '[OCF] Your account has been created!',
            mock.ANY,
        )
        body = send_mail.call_args[0][2]
        assert self.FREE_PRINTING_TEXT in body
        assert self.VHOST_TEXT not in body

    @mock.patch('ocflib.account.creation.send_mail')
    def test_send_created_mail_group(self, send_mail, fake_new_account_request):
        fake_new_account_request = fake_new_account_request._replace(is_group=True)
        send_created_mail(fake_new_account_request)
        send_mail.assert_called_once_with(
            fake_new_account_request.email,
            '[OCF] Your account has been created!',
            mock.ANY,
        )
        body = send_mail.call_args[0][2]
        assert self.FREE_PRINTING_TEXT not in body
        assert self.VHOST_TEXT in body

    @mock.patch('ocflib.account.creation.send_mail')
    def test_send_rejected_mail(self, send_mail, fake_new_account_request):
        send_rejected_mail(fake_new_account_request, 'some reason')
        send_mail.called_called_once_with(
            fake_new_account_request.email,
            '[OCF] Your account has been created!',
            mock.ANY,
        )


class TestPasswordEncryption:

    @pytest.mark.parametrize('password', [
        'hello world',
        'hunter2',
        'mock_send_mail_user.assert_called_once_with',
    ])
    def test_encrypt_decrypt_password(self, password, mock_rsa_key):
        assert decrypt_password(
            encrypt_password(password, RSA.importKey(WEAK_KEY)),
            RSA.importKey(WEAK_KEY),
        ) == password


class TestValidateCallinkOid:

    @pytest.mark.parametrize('oid', [0, 123123123])
    def test_valid_oid(self, oid):
        validate_callink_oid(oid)

    @pytest.mark.parametrize('oid', [46130, 46187])
    def test_invalid_oid(self, oid):
        with pytest.raises(ValidationWarning):
            validate_callink_oid(oid)


class TestValidateEmail:

    @pytest.mark.parametrize('email', [
        'ckuehl@ocf.berkeley.edu',
        'somebody@gmail.com',
        'herp.derp-hello+something@berkeley.edu',
    ])
    def test_valid_email(self, email):
        validate_email(email)

    @pytest.mark.parametrize('email', [
        '',
        '@',
        'hello@hello',
        'some kinda email@gmail.com',
    ])
    def test_invalid_email(self, email):
        with pytest.raises(ValidationError):
            validate_email(email)


class TestValidatePassword:

    @pytest.mark.parametrize('password', [
        'correct horse battery staple',
        'pogjpaioshfoasdfnlka;sdfi;sagj',
        'p@ssw0rd',
    ])
    def test_valid_password(self, password):
        validate_password('ckuehl', password)

    @pytest.mark.parametrize('password', [
        '',
        'simple',
        'correct horse\nbattery staple',
        'correct horse battery staple é',
    ])
    def test_invalid_password(self, password):
        with pytest.raises(ValidationError):
            validate_password('ckuehl', password)


@pytest.yield_fixture
def fake_credentials(mock_rsa_key):
    yield AccountCreationCredentials(
        encryption_key=mock_rsa_key,
        mysql_uri='sqlite://',  # heh
        kerberos_keytab='/nonexist',
        kerberos_principal='create/admin',
        redis_uri='redis://create',
    )


@pytest.yield_fixture
def mock_valid_calnet_uid():
    with mock.patch(
        'ocflib.account.search.user_attrs_ucb',
        return_value={'berkeleyEduAffiliations': ['STUDENT-TYPE-REGISTERED']}
    ):
        yield


@pytest.yield_fixture
def mock_invalid_calnet_uid():
    with mock.patch(
        'ocflib.account.search.user_attrs_ucb',
        return_value={'berkeleyEduAffiliations': ['STUDENT-STATUS-EXPIRED']},
    ):
        yield


class TestValidateRequest:

    def test_valid_request(
        self,
        fake_new_account_request,
        fake_credentials,
        mock_valid_calnet_uid,
        session,
    ):
        assert validate_request(
            fake_new_account_request,
            fake_credentials,
            session,
        ) == ([], [])

    @pytest.mark.parametrize('attrs', [
        {'user_name': 'someuser', 'real_name': 'asdf hjkl'},
        {'callink_oid': 46187, 'is_group': True},
    ])
    def test_invalid_request_warning(
        self,
        fake_new_account_request,
        fake_credentials,
        mock_valid_calnet_uid,
        attrs,
        session,
    ):
        errors, warnings = validate_request(
            fake_new_account_request._replace(**attrs),
            fake_credentials,
            session,
        )
        assert warnings

    @pytest.mark.parametrize('attrs', [
        {'user_name': 'ckuehl'},
    ])
    def test_invalid_request_error(
        self,
        fake_new_account_request,
        fake_credentials,
        mock_valid_calnet_uid,
        attrs,
        session,
    ):
        errors, warnings = validate_request(
            fake_new_account_request._replace(**attrs),
            fake_credentials,
            session,
        )
        assert errors

    def test_invalid_request_already_submitted(
        self,
        fake_new_account_request,
        fake_credentials,
        mock_valid_calnet_uid,
        session,
    ):
        # test where username has already been requested
        with mock.patch('ocflib.account.submission.username_pending', return_value=True):
            errors, warnings = validate_request(
                fake_new_account_request,
                fake_credentials,
                session,
            )
        assert errors

        # test where this user (calnet/callink oid) has already submitted a request
        with mock.patch('ocflib.account.submission.user_has_request_pending', return_value=True):
            errors, warnings = validate_request(
                fake_new_account_request,
                fake_credentials,
                session,
            )
        assert errors


class TestCreateAccount:

    @pytest.mark.parametrize('is_group,calnet_uid,callink_oid,expected', [
        (False, 123456, None, {'calnetUid': ['123456']}),
        (True, None, 123456, {'callinkOid': ['123456']}),
    ])
    def test_create(
        self,
        is_group,
        calnet_uid,
        callink_oid,
        expected,
        fake_new_account_request,
        fake_credentials
    ):
        @contextmanager
        def report_status(start, end, line):
            yield
        with mock.patch('ocflib.account.creation.create_kerberos_principal_with_keytab') as kerberos, \
                mock.patch('ocflib.account.creation.create_ldap_entry_with_keytab') as ldap, \
                mock.patch('ocflib.account.creation.create_home_dir') as home_dir, \
                mock.patch('ocflib.account.creation.create_web_dir') as web_dir, \
                mock.patch('ocflib.account.creation.send_created_mail') as send_created_mail, \
                mock.patch('ocflib.account.creation._get_first_available_uid', return_value=42) as get_uid, \
                mock.patch('ocflib.account.creation.call') as call, \
                freeze_time('2015-08-22 14:11:44'):

            fake_new_account_request = fake_new_account_request._replace(
                is_group=is_group,
                calnet_uid=calnet_uid,
                callink_oid=callink_oid,
            )
            new_uid = create_account(
                fake_new_account_request,
                fake_credentials,
                report_status,
                known_uid=1,
            )
            assert new_uid == 42
            get_uid.assert_called_once_with(1)
            kerberos.assert_called_once_with(
                fake_new_account_request.user_name,
                fake_credentials.kerberos_keytab,
                fake_credentials.kerberos_principal,
                password='hunter2000',
            )
            ldap.assert_called_once_with(
                'uid=someuser,ou=People,dc=OCF,dc=Berkeley,dc=EDU',
                dict({
                    'cn': ['Some User'],
                    'gidNumber': ['1000'],
                    'objectClass': ['ocfAccount', 'account', 'posixAccount'],
                    'uidNumber': ['42'],
                    'homeDirectory': ['/home/s/so/someuser'],
                    'loginShell': ['/bin/bash'],
                    'mail': ['some.user@ocf.berkeley.edu'],
                    'userPassword': ['{SASL}someuser@OCF.BERKELEY.EDU'],
                    'creationTime': ['20150822141144Z'],
                }, **expected),
                fake_credentials.kerberos_keytab,
                fake_credentials.kerberos_principal,
            )
            call.assert_called_once_with(('sudo', 'nscd', '-i', 'passwd'))
            home_dir.assert_called_once_with(fake_new_account_request.user_name)
            web_dir.assert_called_once_with(fake_new_account_request.user_name)
            send_created_mail.assert_called_once_with(fake_new_account_request)
