import os.path
import sys
from contextlib import contextmanager

import mock
import pytest

import ocflib.account.creation
import ocflib.constants as constants
from ocflib.account.creation import _get_first_available_uid
from ocflib.account.creation import create_home_dir
from ocflib.account.creation import create_web_dir
from ocflib.account.creation import eligible_for_account
from ocflib.account.creation import send_created_mail
from ocflib.account.creation import send_rejected_mail
from ocflib.account.creation import validate_calnet_uid
from ocflib.account.creation import validate_username
from ocflib.account.creation import ValidationError
from ocflib.account.creation import ValidationWarning


class TestFirstAvailableUID:

    def test_first_uid(self):
        connection = mock.Mock(response=[
            {'attributes': {'uidNumber': [100]}},
            {'attributes': {'uidNumber': [300]}},
            {'attributes': {'uidNumber': [200]}},
        ])

        @contextmanager
        def ldap_ocf():
            yield connection

        with mock.patch('ocflib.account.creation.ldap_ocf', ldap_ocf):
            next_uid = _get_first_available_uid()

        connection.search.assert_called_with(
            constants.OCF_LDAP_PEOPLE,
            '(uidNumber=*)',
            attributes=['uidNumber'],
        )

        assert next_uid == 301


class TestCreateDirectories:

    @mock.patch('subprocess.check_call')
    def test_create_home_dir(self, check_call):
        create_home_dir('ckuehl')

        calls = [mock.call(
            ['sudo', 'install', '-d', '--mode=0700', '--group=ocf',
                '--owner=ckuehl', '/home/c/ck/ckuehl'],
            stdout=sys.stderr,
        )]

        for name in ['bashrc', 'bash_profile', 'bash_logout']:
            path = os.path.join(os.path.dirname(
                ocflib.account.creation.__file__),
                'rc',
                name,
            )
            calls.append(mock.call(
                ['sudo', 'install', '--mode=0600', '--group=ocf',
                    '--owner=ckuehl', path, '/home/c/ck/ckuehl/.' + name],
                stdout=sys.stderr,
            ))

        check_call.assert_has_calls(calls)

    @mock.patch('subprocess.check_call')
    def test_create_web_dir(self, check_call):
        create_web_dir('ckuehl')
        check_call.assert_called_with(
            ['sudo', 'install', '-d', '--mode=0000', '--group=ocf',
                '--owner=ckuehl', '/services/http/users/c/ckuehl'],
            stdout=sys.stderr)


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
        'hella',
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

    @mock.patch(
        'ocflib.account.search.user_attrs_ucb',
        return_value={'berkeleyEduAffiliations': ['STUDENT-TYPE-REGISTERED']}
    )
    def test_validate_calnet_uid_success(self, _):
        validate_calnet_uid(9999999999999)

    @mock.patch(
        'ocflib.account.search.user_attrs_ucb',
        return_value={'berkeleyEduAffiliations': ['STUDENT-STATUS-EXPIRED']},
    )
    def test_validate_calnet_affiliations_failure(self, _):
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
        (['STUDENT-TYPE-REGISTERED', 'STUDENT-STATUS-EXPIRED'], False),
        (['STUDENT-STATUS-EXPIRED'], False),

        ([], False),
    ])
    def test_affiliations(self, affiliations, eligible):
        assert eligible_for_account(affiliations) == eligible


class TestSendMail:

    @mock.patch('ocflib.misc.mail.send_mail')
    def test_send_created_mail(self, send_mail):
        send_created_mail('email', 'realname', 'username')
        assert send_mail.called

    @mock.patch('ocflib.misc.mail.send_mail')
    def test_send_rejected_mail(self, send_mail):
        send_rejected_mail('email', 'realname', 'username', 'reason')
        assert send_mail.called
