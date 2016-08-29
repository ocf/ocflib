import pytest

from ocflib.misc.validators import email_host_exists
from ocflib.misc.validators import host_exists
from ocflib.misc.validators import valid_email
from ocflib.misc.validators import valid_login_shell


REAL_HOSTS = [
    'ocf.berkeley.edu',
    'google.com',
    'dev-ocf.berkeley.edu',
    'mirrors.berkeley.edu',
    'cs.berkeley.edu',
    'cory.eecs.berkeley.edu',
    'g.berkeley.edu',
]
FAKE_HOSTS = [
    'hello.waffle',
    'i am not a real host',
    'lashdfkjashgklhsadfsad.com',
    'asdfghjkl.eecs.berkeley.edu',
    'asdfghjkl.berkeley.edu',
    'kljasdlgjlsafdfhsadf.berkeley.edu',
    'jf0194y89v(*#14o1i9XC',
    '@I$)!($U)!#Y%!)#()*(%!#',
    'vns;alf iashf poasf bawen svn;',
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


@pytest.mark.parametrize('shell,valid', [
    ('/bin/sh', True),
    ('/bin/bash', True),
    ('/bin/dash', True),
    ('/bin/trash', False),
    ('/bin/rbash', True),
    ('/bin/tcsh', True),
    ('/bin/zsh', True),
    ('/usr/bin/screen', True),
    ('/usr/bin/tmux', True),
    ('bash', False),
])
def test_valid_login_shell(shell, valid):
    assert valid_login_shell(shell) == valid
