"""Announcements handling"""
from datetime import datetime

from requests import get
from yaml import safe_load

# The default branch is main
ANNOUNCEMENTS_URL = (
    'https://api.github.com/repos/ocf/announcements/contents/{folder}/{id}'
)
# 1 day in seconds
TIME_TO_LIVE = 60 * 60 * 24


class Metadata:
    def __init__(self, title, date, author, tags, summary):
        self.title = title
        self.date = date
        self.author = author
        self.tags = tags
        self.summary = summary


class _AnnouncementCache:
    def __init__(self) -> None:
        # post_cache is a dict of {id: post content}
        self.cache = {}
        self.last_updated = datetime.now()

    def clear_cache(self) -> None:
        """Clear the cache if it's too old"""

        if (datetime.now() - self.last_updated).total_seconds() > TIME_TO_LIVE:
            self.cache.clear()
            self.last_updated = datetime.now()


_announcement_cache_instance = _AnnouncementCache()


def _check_id(id: str) -> bool:
    """Check if the id is a valid date"""

    try:
        datetime.strptime(id, '%Y-%m-%d-%M')
    except ValueError:
        raise ValueError('Invalid id')


def get_all_announcements(folder='announcements') -> [dict]:
    """
    Get announcements from the announcements repo
    The result is a list of post metadatas
    """

    posts = get(
        url=ANNOUNCEMENTS_URL.format(folder=folder, id=''),
        headers={'Accept': 'application/vnd.github+json'},
    )
    posts.raise_for_status()

    return posts.json()


def get_announcement(id: str, folder='announcements') -> str:
    """
    Get one particular announcement from the announcements repo
    The result is the post content
    """

    _check_id(id)
    # check if the cache is too old
    _announcement_cache_instance.clear_cache()

    if id in _announcement_cache_instance.cache:
        return _announcement_cache_instance.cache[id]

    post = get(
        url=ANNOUNCEMENTS_URL.format(folder=folder, id=id + '.md'),
        headers={'Accept': 'application/vnd.github.raw'},
    )
    post.raise_for_status()

    _announcement_cache_instance.cache[id] = post.text

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

        data = Metadata(
            title=meta_dict['title'],
            date=meta_dict['date'],
            author=meta_dict['author'],
            tags=meta_dict['tags'],
            summary=meta_dict['summary'],
        )
    except (IndexError, KeyError) as e:
        raise ValueError(f'Error parsing metadata: {e}')

    return data


def get_last_n_announcements_text(n: int) -> [str]:
    """Get the text of last n announcements"""

    assert n > 0, 'n must be positive'

    result = []

    # the res returned are in reverse chronological order
    # so we need to reverse it first then take the first n
    res = get_all_announcements()[::-1][:n]

    for item in res:
        result.append(get_announcement(get_id(item)))

    return result
