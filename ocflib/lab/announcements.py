"""Announcements handling"""
import requests
import json

ANNOUNCEMENTS_REPO = (
    "https://api.github.com/repos/ocf/announcements/contents/announcements/{id}"
)


def get_all_announcements() -> str:
    """Get announcements from the announcements repo"""
    r = requests.get(
        url=ANNOUNCEMENTS_REPO.format(id=""),
        headers={"Accept": "application/vnd.github+json"},
    )
    r.raise_for_status()

    return json.dumps(r.json(), indent=4)


def get_announcement(id: str) -> str:
    """Get one particular announcement from the announcements repo"""
    r = requests.get(
        url=ANNOUNCEMENTS_REPO.format(id=id + ".md"),
        headers={"Accept": "application/vnd.github.raw"},
    )
    r.raise_for_status()

    return r.text


def get_metadata(post: str) -> str:
    """Get the metadata from one announcement"""
    return post.split("---")[1]


print(get_all_announcements())
print(get_announcement("2002-01-01-00"))
print(get_metadata(get_announcement("2002-01-01-00")))
