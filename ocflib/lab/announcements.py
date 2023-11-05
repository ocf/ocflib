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


def get_metadata(id: str) -> Metadata:
    """Get the metadata from one announcement"""
    post = get_announcement(id)
    meta_dict = safe_load(post.split("---")[1])

    metadata = Metadata(
        title=meta_dict["title"],
        date=meta_dict["date"],
        author=meta_dict["author"],
        tags=meta_dict["tags"],
        summary=meta_dict["summary"],
    )
    return metadata


def get_all_ids():
    """Get all announcement ids"""
    posts = get_all_announcements()
    return [post["name"][:-3] for post in posts]


def get_ids(num: int):
    """Get the last num announcement ids"""
    posts = get_all_announcements()
    return [post["name"][:-3] for post in posts[:num]]


# print(get_all_announcements())
# print(get_announcement("2002-01-01-00"))
# print(get_metadata("2002-01-01-00"))
# print(get_all_ids())
