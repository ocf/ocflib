#!/usr/bin/env python3
"""Print the ocfprinting DB schema, to be piped to mysql."""
from ocflib.printing.quota import get_schema


if __name__ == '__main__':
    print(get_schema())
