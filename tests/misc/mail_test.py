import subprocess
from email.parser import Parser

import mock
import pytest

from ocflib.constants import MAIL_ROOT
from ocflib.constants import SENDMAIL_PATH
from ocflib.misc.mail import email_for_user
from ocflib.misc.mail import send_mail
from ocflib.misc.mail import send_mail_user
from ocflib.misc.mail import send_problem_report


class TestEmailForUser:

    @pytest.mark.parametrize('username,email', [
        ('ckuehl', 'ckuehl@ocf.berkeley.edu'),
        ('daradib', 'daradib@ocf.berkeley.edu'),
    ])
    def test_existant(self, username, email):
        assert email_for_user(username) == email

    def test_nonexistant(self):
        with pytest.raises(ValueError):
            assert email_for_user('nonexist')


@pytest.yield_fixture
def mock_popen():
    with mock.patch('subprocess.Popen') as popen:
        yield popen


class TestEmailSending:

    def get_message(self, mock_popen):
        mock_popen.assert_called_with(
            (SENDMAIL_PATH, '-t', '-oi'),
            stdin=subprocess.PIPE,
        )

        calls = mock_popen.return_value.communicate.call_args_list
        assert len(calls) == 1

        return Parser().parsestr(calls[0][0][0].decode('utf8'))

    def test_send_mail(self, mock_popen):
        send_mail(
            'devnull@ocf.berkeley.edu',
            'hello world',
            'this is a body',
            sender='ocflib <help@ocf.berkeley.edu>',
        )

        msg = self.get_message(mock_popen)
        assert msg['Subject'] == 'hello world'
        assert msg['From'] == 'ocflib <help@ocf.berkeley.edu>'
        assert msg['To'] == 'devnull@ocf.berkeley.edu'
        assert msg.get_payload() == 'this is a body'

    def test_send_mail_user(self, mock_popen):
        send_mail_user(
            'ckuehl',
            'hello world',
            'this is a body',
            sender='ocflib <help@ocf.berkeley.edu>',
        )

        msg = self.get_message(mock_popen)
        assert msg['Subject'] == 'hello world'
        assert msg['From'] == 'ocflib <help@ocf.berkeley.edu>'
        assert msg['To'] == 'ckuehl@ocf.berkeley.edu'
        assert msg.get_payload() == 'this is a body'

    @pytest.mark.parametrize('sender,recipient', [
        ('not@a.real@email', 'ggroup@ocf.berkeley.edu'),
        ('ggroup@ocf.berkeley.edu', 'not@a.real@email'),
    ])
    def test_send_mail_errors(self, sender, recipient, mock_popen):
        with pytest.raises(ValueError):
            send_mail(sender, 'subject', 'body', sender=recipient)
        assert not mock_popen.called

    def test_problem_report(self, mock_popen):
        send_problem_report('hellllo world')

        msg = self.get_message(mock_popen)
        assert msg['Subject'].startswith('[ocflib] Problem report')
        assert msg['From'] == 'ocflib <root@ocf.berkeley.edu>'
        assert msg['To'] == MAIL_ROOT
        assert 'hellllo world' in msg.get_payload()
