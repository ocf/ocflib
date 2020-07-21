#!/usr/bin/env python3
"""Print the quota of a user."""
from ocflib.printing.quota import get_connection
from ocflib.printing.quota import get_quota


if __name__ == "__main__":
    with get_connection() as c:
        print(get_quota(c, input("user: ")))
