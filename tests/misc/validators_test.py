import pytest

from ocflib.misc.validators import email_host_exists
from ocflib.misc.validators import host_exists
from ocflib.misc.validators import valid_email


REAL_HOSTS = ['ocf.berkeley.edu', 'google.com']
FAKE_HOSTS = [
    'hello.waffle',
    'i am not a real host',
    'lashdfkjashgklhsadfsad.com',
]


@pytest.mark.parametrize(
    'host,exists',
    [(host, True) for host in REAL_HOSTS] +
    [(host, False) for host in FAKE_HOSTS]
)
def test_host_exists(host, exists):
    assert host_exists(host) == exists


@pytest.mark.parametrize(
    'email,exists',
    [('ckuehl@' + host, True) for host in REAL_HOSTS] +
    [('ckuehl@' + host, False) for host in FAKE_HOSTS] +
    [('no host here!', False)],
)
def test_email_host_exists(email, exists):
    assert email_host_exists(email) == exists


@pytest.mark.parametrize('email,valid', [
    ('ckuehl@ocf.berkeley.edu', True),
    ('hello-world_i+am.email@google.com', True),
    ('hello world@ocf.berkeley.edu', False),
    ('hello world@ocf', False),
    ('derp@langasdgkjsadhglkjbjgsdfgsd.com', False),
    ('derp@www.ocf.berkeley.edu', False),  # no MX records
    ('@ocf', False),
    ('hello@', False),
    ('@', False),
    ('', False),
])
def test_valid_email(email, valid):
    assert valid_email(email) == valid
