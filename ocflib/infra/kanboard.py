"""Print Kanboard task information."""
from collections import namedtuple

import json
import requests


KANBOARD_ROOT = 'https://kanboard.ocf.berkeley.edu'


def request(usr, api_key, method, params):
    payload = json.dumps({'jsonrpc': '2.0', 'method': method, 'id': 1, 'params': params})
    return requests.post(
               '{}/jsonrpc.php'.format(KANBOARD_ROOT),
               data=payload,
               auth=(usr, api_key),
               timeout=10,
           )


class KanboardError(ValueError):
    pass


class KanboardTask(namedtuple('KanboardTask', ('number', 'title', 'creator', 'project'))):
    """A namedtuple representing a Kanboard task."""

    def __str__(self):
        return (
            'k#{self.number}: "{self.title}" | '
            '{self.project}, started by {self.creator} | '
            'https://ocf.io/k/{self.number}'
        ).format(self=self)

    @classmethod
    def from_number(cls, usr, api_key, num):
        task_resp = request(usr, api_key, 'getTask', {'task_id': num})
        if task_resp.status_code != 200:
            raise KanboardError(
                'Task request gave {}'.format(task_resp.status_code)
            )

        task = task_resp.json()['result']

        users_resp = request(usr, api_key, 'getProjectUsers', {'project_id': task['project_id']})
        if users_resp.status_code != 200:
            raise KanboardError(
                'Project request gave {}'.format(users_resp.status_code)
            )

        users = users_resp.json()['result']

        proj_resp = request(usr, api_key, 'getProjectById', {'project_id': task['project_id']})
        if proj_resp.status_code != 200:
            raise KanboardError(
                'Project request gave {}'.format(proj_resp.status_code)
            )

        proj = proj_resp.json()['result']

        return cls(
            number=task['id'],
            title=task['title'],
            creator=users[task['creator_id']],
            project=proj['name'],
        )
