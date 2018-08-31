"""Print Discourse topic information."""
from collections import namedtuple

import requests


class DiscourseTopic(namedtuple('DiscourseTopic', ('number', 'title', 'starter', 'category'))):
    """A namedtuple representing a Discourse topic."""

    def __str__(self):
        return (
            't#{self.number}: "{self.title}" | '
            '{self.category}, started by {self.starter} | '
            'https://ocf.io/t/{self.number}'
        ).format(self=self)

    @classmethod
    def from_number(cls, api_key, num):
        params = {'api_key': api_key, 'api_username': 'gstaff'}

        topic_resp = requests.get(
            'https://discourse.ocf.berkeley.edu/t/{}.json'.format(num),
            params=params
        )
        assert topic_resp.status_code == 200, topic_resp.status_code
        topic = topic_resp.json()

        category_id = topic['category_id']

        cat_resp = requests.get(
            'https://discourse.ocf.berkeley.edu/categories.json',
            params=params
        )
        assert cat_resp.status_code == 200, cat_resp.status_code
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
