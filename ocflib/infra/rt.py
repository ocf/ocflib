import re
from collections import namedtuple
from urllib.parse import urlencode

import requests
import json
import copy


class RtTicket(namedtuple('RtTicket', ('number', 'owner', 'subject', 'queue', 'status'))):
    """A namedtuple representing an RT ticket."""

    def __str__(self):
        return (
            'rt#{self.number}: "{self.subject}" | '
            '{self.queue}, {self.status}, owned by {self.owner} | '
            'https://ocf.io/rt/{self.number}'
        ).format(self=self)

    @classmethod
    def from_number(cls, _, num, auth):
        """
        Second argument left for compatibility purposes, alghough I think no programme
        ever used this function when I wrote this, lol
        """
        resp = requests.get("https://rt.ocf.berkeley.edu/REST/2.0/ticket/{0}".format(num), **auth)
        assert resp.ok, resp.status_code
        assert '200 Ok' in resp.text

        jsonified = resp.json()

        return cls(
            number=jsonified["id"],
            owner=jsonified["Owner"],
            subject=jsonified["Subject"],
            queue=jsonified["Queue"],
            status=jsonified["Status"],
        )

    @classmethod
    def get_latest(cls, _, queue, auth):
        """
        Second argument left for compatibility purposes, alghough I think no programme
        ever used this function when I wrote this, lol
        """
        resp = requests.get("https://rt.ocf.berkeley.edu/REST/2.0/tickets?query=Queue='{}'&orderby=Created&order=DESC".format(queue), **auth)
        assert resp.ok, resp.status_code
        assert '200 Ok' in resp.text


        jsonified = resp.json()
        assert "items" in jsonified
        assert len(jsonified["items"]) > 0

        jsonified = jsonified["items"][0]

        return cls(
            number=jsonified["id"],
            owner=jsonified["Owner"],
            subject=jsonified["Subject"],
            queue=jsonified["Queue"],
            status=jsonified["Status"],
        )

    @classmethod
    def create(cls, _, queue, requestor, subject, text, auth, **kwargs):
        """Create an RT ticket and returns an instance of the result"""
        # RT prefixes multiline strings by a blank space
        text = text.replace('\n', '\n ')

        data = {
            'Queue': queue,
            'Requestor': requestor,
            'Subject': subject,
            'Text': text,
            **kwargs,
        }

        # Look like crap but it works?
        # There must be some more elegant way but idk
        additional_kwargs = copy.deepcopy(auth)
        if "headers" not in additional_kwargs:
            additional_kwargs["headers"] = {}
        additional_kwargs["headers"]["content-type"] = "application/json"

        resp = requests.post('https://rt.ocf.berkeley.edu/REST/2.0/ticket', json=data, **additional_kwargs)
        resp.raise_for_status()
        assert '200 Ok' in resp.text

        assert "id" in resp.json(), '200 response but no ticket number found in RT response'

        return resp.json()["id"]


def rt_connection_auth(*args):
    """Return the authentication required to access REST API.

    Accepts either a RtCredentials, a RtAuthenticationToken, a string (as token),
    or two strings (as username and password)

    Currently, we only enable access to the REST API from a few select IPs.
    """
    if len(args) == 1:
        if isinstance(args[0], RtCredentials): 
            return {"auth": (args[0]["username"], args[0]["password"])}
        elif isinstance(args[0], RtAuthenticationToken):
            return {"headers": {"Authorization": "token {}".format(args[0]["token"])}}
        elif isinstance(args[0], str):
            return {"headers": {"Authorization": "token {}".format(args[0])}}
    elif len(args) == 2 and all(map(lambda e: isinstance(e, str), args)):
        return  {"auth": (args[0], args[1])}
    raise ValueError("Auth credential provided is not valid")



class RtCredentials(namedtuple('RtCredentials', [
    'username',
    'password',
])):
    """Credentials for programmatically accessing RT.

    :param username: str
    :param password: str
    """

class RtAuthenticationToken(namedtuple('RtAuthenticationToken', [
    'token'
])):
    """Token for programmatically accessing RT.

    :param token: str
    """
