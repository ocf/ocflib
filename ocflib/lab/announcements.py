"""Announcements handling"""
from collections import deque
from collections import namedtuple
from datetime import datetime
from typing import Dict

from requests import get
from yaml import safe_load

# The default branch is main
ANNOUNCEMENTS_URL = (
    'https://api.github.com/repos/ocf/announcements/contents/{folder}/{id}'
)
CACHE_LEN = 10

# post_cache is a dict of {id: post content}
post_cache: Dict[str, str] = {}
id_cache = deque(maxlen=CACHE_LEN)
Metadata = namedtuple('Metadata', ['title', 'date', 'author', 'tags', 'summary'])


def _check_id(id: str) -> bool:
    """Check if the id is a valid date"""

    try:
        datetime.strptime(id, '%Y-%m-%d-%M')  # TODO: if this %M (minute) is sufficient
    except ValueError:
        raise ValueError('Invalid id')


def get_all_announcements(folder='announcements') -> [dict]:
    """Get announcements from the announcements repo"""

    posts = get(
        url=ANNOUNCEMENTS_URL.format(folder=folder, id=''),
        headers={'Accept': 'application/vnd.github+json'},
    )
    posts.raise_for_status()

    return posts.json()


def get_announcement(id: str, folder='announcements') -> str:
    """Get one particular announcement from the announcements repo"""

    _check_id(id)

    if id in post_cache:
        return post_cache[id]

    post = get(
        url=ANNOUNCEMENTS_URL.format(folder=folder, id=id + '.md'),
        headers={'Accept': 'application/vnd.github.raw'},
    )
    post.raise_for_status()

    post_cache[id] = post.text

    # add the most recent id to the left of the deque
    if id not in id_cache:
        id_cache.appendleft(id)

    return post.text


def get_id(post_json: dict) -> str:
    """Get announcement id based on the json response"""

    # Since the id is the filename, remove the .md extension
    try:
        id = post_json['name'][:-3]
    except KeyError:
        raise KeyError('Missing id in announcement')

    _check_id(id)

    return id


def get_metadata(post_text: str) -> Metadata:
    """Get the metadata from one announcement"""

    try:
        meta_dict = safe_load(post_text.split('---')[1])
    except IndexError:
        raise IndexError('Missing metadata in announcement')

    try:
        metadata = Metadata(
            title=meta_dict['title'],
            date=meta_dict['date'],
            author=meta_dict['author'],
            tags=meta_dict['tags'],
            summary=meta_dict['summary'],
        )
    except KeyError:
        raise KeyError('Missing metadata in announcement')

    return metadata


def get_last_n_announcements_text(n: int) -> [str]:
    """Get the text of last n announcements"""

    assert n > 0, 'n must be positive'

    result = []

    # Get announcements from the cache (latest first)
    for id in list(id_cache)[:n]:
        result.append(post_cache[id])

    # Fetch additional announcements if needed
    if n > CACHE_LEN:
        posts = get_all_announcements()
        needed = n - CACHE_LEN

        # The posts returned are in reverse chronological order
        # So we first need to grab the last CACHE_LEN + 1 posts to avoid duplicates
        # Then we need to reverse the order and grab the first needed posts
        for post in posts[-CACHE_LEN - 1:: -1][:needed]:
            result.append(get_announcement(get_id(post)))

    return result
