"""Print Discourse topic information."""
from collections import namedtuple

import requests


DISCOURSE_ROOT = 'https://discourse.ocf.berkeley.edu'


class DiscourseError(ValueError):
    pass


class DiscourseTopic(namedtuple('DiscourseTopic', ('number', 'title', 'starter', 'category'))):
    """A namedtuple representing a Discourse topic."""

    def __str__(self):
        return (
            'd#{self.number}: "{self.title}" | '
            '{self.category}, started by {self.starter} | '
            'https://ocf.io/d/{self.number}'
        ).format(self=self)

    @classmethod
    def from_number(cls, api_key, num):
        params = {'api_key': api_key, 'api_username': 'gstaff'}

        topic_resp = requests.get(
            '{}/t/{}.json'.format(DISCOURSE_ROOT, num),
            params=params,
            timeout=10,
        )
        if topic_resp.status_code != 200:
            raise DiscourseError(
                'Topic request gave {}'.format(topic_resp.status_code)
            )

        topic = topic_resp.json()

        category_id = topic['category_id']

        cat_resp = requests.get(
            '{}/categories.json'.format(DISCOURSE_ROOT),
            params=params,
            timeout=10,
        )
        if cat_resp.status_code != 200:
            raise DiscourseError(
                'Category request gave {}'.format(cat_resp.status_code)
            )

        categories = cat_resp.json()

        cat_name = next(
            cat['name']
            for cat in categories['category_list']['categories']
            if cat['id'] == category_id
        )

        return cls(
            number=topic['id'],
            title=topic['title'],
            starter=topic['details']['created_by']['username'],
            category=cat_name,
        )
