#!/usr/bin/env python3
"""Add a test job."""
from ocflib.printing.quota import get_connection
from ocflib.printing.quota import get_quota


if __name__ == '__main__':
    with get_connection() as c:
        print(get_quota(c, input('user: ')))
