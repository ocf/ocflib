"""Announcements handling"""
from collections import namedtuple
from requests import get

from yaml import safe_load
from typing import NamedTuple

ANNOUNCEMENTS_REPO = (
    "https://api.github.com/repos/ocf/announcements/contents/announcements/{id}"
)

# TODO: cache
# TODO: request session for better efficiency

Metadata = namedtuple("Metadata", ["title", "date", "author", "tags", "summary"])


def get_all_announcements():
    """Get announcements from the announcements repo"""
    posts = get(
        url=ANNOUNCEMENTS_REPO.format(id=""),
        headers={"Accept": "application/vnd.github+json"},
    )
    posts.raise_for_status()

    return posts.json()


def get_announcement(id: str) -> str:
    """Get one particular announcement from the announcements repo"""
    posts = get(
        url=ANNOUNCEMENTS_REPO.format(id=id + ".md"),
        headers={"Accept": "application/vnd.github.raw"},
    )
    posts.raise_for_status()

    return posts.text


def get_id(post: str) -> str:
    """Get announcement id"""
    return post["name"][:-3]


def get_metadata(post: str) -> Metadata:
    """Get the metadata from one announcement"""
    meta_dict = safe_load(post.split("---")[1])

    metadata = Metadata(
        title=meta_dict["title"],
        date=meta_dict["date"],
        author=meta_dict["author"],
        tags=meta_dict["tags"],
        summary=meta_dict["summary"],
    )
    return metadata


def get_announcements(num: int) -> list[str]:
    """Get the last num announcements"""
    posts = get_all_announcements()

    # get the last num posts in reverse order
    return [get_announcement(get_id(post)) for post in posts[-1 : -num - 1 : -1]]


# print(get_all_announcements())
# print(get_announcement("2002-01-01-00"))
# print(get_metadata(get_announcement("2002-01-01-00")))
# print(get_all_ids())
# print(get_announcements(2))
