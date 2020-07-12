import re
from collections import namedtuple
from urllib.parse import urlencode

import requests


class RtTicket(namedtuple('RtTicket', ('number', 'owner', 'subject', 'queue', 'status'))):
    """A namedtuple representing an RT ticket."""

    def __str__(self):
        return (
            'rt#{self.number}: "{self.subject}" | '
            '{self.queue}, {self.status}, owned by {self.owner} | '
            'https://ocf.io/rt/{self.number}'
        ).format(self=self)

    @classmethod
    def from_number(cls, connection, num):
        resp = connection.get('https://rt.ocf.berkeley.edu/REST/1.0/ticket/{}/view'.format(num))
        assert resp.status_code == 200, resp.status_code
        assert '200 Ok' in resp.text

        lines = resp.text.splitlines()

        def find(header):
            for line in lines:
                if line.startswith(header + ': '):
                    return line.split(': ', 1)[1]

        return cls(
            number=num,
            owner=find('Owner'),
            subject=find('Subject'),
            queue=find('Queue'),
            status=find('Status'),
        )

    @classmethod
    def create(cls, connection, queue, requestor, subject, text, **kwargs):
        """Create an RT ticket and returns an instance of the result"""
        # RT prefixes multiline strings by a blank space
        text = text.replace('\n', '\n ')

        data = {
            'id': 'ticket/new',
            'Queue': queue,
            'Requestor': requestor,
            'Subject': subject,
            'Text': text,
            **kwargs,
        }

        # RT's incoming data format has the form key: value, but these aren't HTTP Headers
        body = ''
        for k, v in data.items():
            body += '{}: {}\n'.format(k, v)

        # RT requires the POST content to be sent with no filename hence 'content': (None, body)
        resp = connection.post('https://rt.ocf.berkeley.edu/REST/1.0/ticket/new', files={'content': (None, body)})
        resp.raise_for_status()
        assert '200 Ok' in resp.text

        match = re.search(r'Ticket ([0-9]+) created.', resp.text)
        assert match, '200 response but no ticket number found in RT response'

        ticket_number = int(match.group(1))
        return ticket_number


def rt_connection(user, password):
    """Return a requests Session object authenticated against RT.

    Currently, we only enable access to the REST API from a few select IPs.
    """
    s = requests.Session()
    resp = s.post(
        'https://rt.ocf.berkeley.edu/REST/1.0/',
        data=urlencode({'user': user, 'pass': password}),
        timeout=20,
    )
    assert resp.status_code == 200, resp.status_code
    assert '200 Ok' in resp.text
    return s


class RtCredentials(namedtuple('RtCredentials', [
    'username',
    'password',
])):
    """Credentials for programmatically accessing RT.

    :param username: str
    :param password: str
    """
