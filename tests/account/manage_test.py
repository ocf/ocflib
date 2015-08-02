import fcntl

import mock
import pytest
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

from ocflib.account.manage import _notify_password_change
from ocflib.account.manage import change_password_with_keytab
from ocflib.account.manage import change_password_with_staffer
from ocflib.account.manage import encrypt_password
from ocflib.account.manage import queue_creation
from ocflib.account.manage import trigger_create


@pytest.yield_fixture
def mock_spawn():
    with mock.patch('pexpect.spawn') as spawn:
        yield spawn


@pytest.yield_fixture
def mock_notify_password_change():
    with mock.patch(
        'ocflib.account.manage._notify_password_change',
    ) as _notify_password_change:
        yield _notify_password_change


class TestChangePasswordWithStaffer:

    def _chpass(self, mock_spawn):
        change_password_with_staffer(
            'ggroup',
            'strong_hunter2',
            'ckuehl/admin',
            'super_hunter2',
        )
        mock_spawn.assert_called_with(
            '/usr/bin/kadmin -p ckuehl/admin cpw ggroup',
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('strong_hunter2'), mock.call('strong_hunter2')],
        )

    def test_success(self, mock_spawn, mock_notify_password_change):
        self._chpass(mock_spawn)
        mock_notify_password_change.assert_called_once_with('ggroup')

    @pytest.mark.parametrize('error', [
        'kadmin: cpw ggroup: Looping detected inside krb5_get_in_tkt',
        'kadmin: some random error you do not expect',
    ])
    def test_kadmin_failure(
        self,
        error,
        mock_spawn,
        mock_notify_password_change,
    ):
        mock_spawn.return_value.before.decode.return_value = error
        with pytest.raises(ValueError):
            self._chpass(mock_spawn)
        assert not mock_notify_password_change.called


class TestChangePasswordWithKeytab:

    def _chpass(self, mock_spawn):
        change_password_with_keytab(
            'ggroup',
            'strong_hunter2',
            '/some/keytab',
            'create/admin',
        )
        mock_spawn.assert_called_with(
            '/usr/bin/kadmin -K /some/keytab -p create/admin cpw ggroup',
            timeout=10,
        )
        mock_spawn.return_value.sendline.assert_has_calls(
            [mock.call('strong_hunter2'), mock.call('strong_hunter2')],
        )

    def test_success(self, mock_spawn, mock_notify_password_change):
        self._chpass(mock_spawn)
        mock_notify_password_change.assert_called_once_with('ggroup')

    def test_kadmin_failure(self, mock_spawn, mock_notify_password_change):
        mock_spawn.return_value.before.decode.return_value = (
            'kadmin: cpw ggroup: Looping detected inside krb5_get_in_tkt'
        )
        with pytest.raises(ValueError):
            self._chpass(mock_spawn)
        assert not mock_notify_password_change.called


@mock.patch('ocflib.misc.mail.send_mail_user')
def test_notify_password_change(mock_send_mail_user):
    _notify_password_change('ckuehl')
    mock_send_mail_user.assert_called_once_with('ckuehl', mock.ANY, mock.ANY)


@mock.patch('paramiko.RSAKey')
@mock.patch('paramiko.SSHClient')
def test_trigger_create(SSHClient, RSAKey):
    trigger_create('/some/private/key', '/some/host/keys')

    ssh = SSHClient()
    ssh.load_host_keys.assert_called_with('/some/host/keys')
    ssh.connect.assert_called_once_with(
        hostname='admin.ocf.berkeley.edu',
        username='atool',
        pkey=RSAKey.from_private_key_file('/some/private_key'),
    )
    ssh.exec_command.assert_called_once_with('/srv/atool/bin/create')


WEAK_KEY = """-----BEGIN RSA PRIVATE KEY-----
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


@pytest.yield_fixture
def mock_rsa_key():
    real_key = RSA.importKey(WEAK_KEY)
    with mock.patch('builtins.open', mock.mock_open(read_data=WEAK_KEY)):
        yield real_key


@pytest.mark.parametrize('password', [
    'hello world',
    'hunter2',
    'mock_send_mail_user.assert_called_once_with',
])
def test_encrypt_password(password, mock_rsa_key):
    RSA_CIPHER = PKCS1_OAEP.new(mock_rsa_key)
    password = password.encode('utf8')
    assert RSA_CIPHER.decrypt(encrypt_password(password)) == password


class TestQueueCreation:

    @pytest.mark.parametrize('name,calnet,callink,username,email,password', [
        # both calnet uid and callink oid
        ('Chris', 100, 100, 'nonexist', 'a@gmail.com', '9cy9APmA'),

        # neither calnet uid or callink oid
        ('Chris', None, None, 'nonexist', 'a@gmail.com', '9cy9APmA'),

        # username already exists
        ('Chris', 100, None, 'ckuehl', 'a@gmail.com', '9cy9APmA'),

        # username already queued
        ('Chris', 100, None, 'imqueued', 'a@gmail.com', '9cy9APmA'),

        # username reserved
        ('Chris', 100, None, 'ocfwiki', 'an@gmail.com', '9cy9APmA'),

        # name too short
        ('Hi', 100, None, 'nonexist', 'a@gmail.com', '9cy9APmA'),

        # invalid email
        ('Chris', 100, None, 'nonexist', 'this aint no email', '9cy9APmA'),
    ])
    def test_bad_users(self, name, calnet, callink, username, email, password):
        with pytest.raises(ValueError), mock.patch(
            'ocflib.account.validators.username_queued',
            return_value=(username == 'imqueued'),
        ):
            queue_creation(name, calnet, callink, username, email, password)

    @mock.patch('fcntl.flock')
    @mock.patch('ocflib.misc.validators.valid_email', return_value=True)
    @mock.patch('ocflib.account.manage.encrypt_password', return_value=b'hi')
    @mock.patch('builtins.print')
    def test_success(self, mock_print, mock_email, mock_encrypt, mock_flock):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            queue_creation(
                'Chris Kuehl',
                100,
                None,
                'nonexist',
                'ckuehl@ocf.berkeley.edu',
                'some strong password',
            )
            mock_flock.assert_has_calls([
                mock.call(mock_open(), fcntl.LOCK_EX),
                mock.call(mock_open(), fcntl.LOCK_UN),
            ] * 2)
            assert mock_print.call_count == 2
