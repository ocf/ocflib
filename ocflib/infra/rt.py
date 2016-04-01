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


def rt_connection(user, password):
    """Return a requests Session object authenticated against RT.

    Currently, we only enable access to the REST API from a few select IPs.
    """
    s = requests.Session()
    resp = s.post(
        'https://rt.ocf.berkeley.edu/REST/1.0/',
        data=urlencode({'user': user, 'pass': password}),
    )
    assert resp.status_code == 200, resp.status_code
    assert '200 Ok' in resp.text
    return s
