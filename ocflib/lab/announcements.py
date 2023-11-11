"""Announcements handling"""
from collections import namedtuple
from requests import get
from datetime import datetime
from yaml import safe_load
from collections import deque

# The default branch is main
ANNOUNCEMENTS_URL = (
    "https://api.github.com/repos/ocf/announcements/contents/announcements/{id}"
)
CACHE_LEN = 10

# post_cache is a dict of id: post
post_cache = {}
id_cache = deque(maxlen=CACHE_LEN)


Metadata = namedtuple("Metadata", ["title", "date", "author", "tags", "summary"])


def get_all_announcements() -> list[dict]:
    """Get announcements from the announcements repo"""

    posts = get(
        url=ANNOUNCEMENTS_URL.format(id=""),
        headers={"Accept": "application/vnd.github+json"},
    )
    posts.raise_for_status()

    return posts.json()


def get_announcement(id: str) -> str:
    """Get one particular announcement from the announcements repo"""

    if id in post_cache:
        return post_cache[id]

    posts = get(
        url=ANNOUNCEMENTS_URL.format(id=id + ".md"),
        headers={"Accept": "application/vnd.github.raw"},
    )
    posts.raise_for_status()

    post_cache[id] = posts.text

    # add the most recent id to the left of the deque
    if id not in id_cache:
        id_cache.appendleft(id)

    return posts.text


def get_id(post: dict) -> str:
    """Get announcement id based on the json response"""

    # Since the id is the filename, remove the .md extension
    try:
        id = post["name"][:-3]
    except KeyError:
        raise KeyError("Missing id in announcement")

    # Check if the id is a valid date
    try:
        datetime.strptime(id, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid announcement id")

    return id


def get_metadata(post: str) -> Metadata:
    """Get the metadata from one announcement"""

    try:
        meta_dict = safe_load(post.split("---")[1])
    except IndexError:
        raise IndexError("Missing metadata in announcement")

    try:
        metadata = Metadata(
            title=meta_dict["title"],
            date=meta_dict["date"],
            author=meta_dict["author"],
            tags=meta_dict["tags"],
            summary=meta_dict["summary"],
        )
    except KeyError:
        raise KeyError("Missing metadata in announcement")

    return metadata


def get_last_n_announcements(n: int) -> list[str]:
    """Get the last n announcements"""

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
        for post in posts[-CACHE_LEN - 1 :: -1][:needed]:
            result.append(get_announcement(get_id(post)))

    return result
