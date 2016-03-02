#!/usr/bin/env python3
"""Initialize the ocfprinting DB schema."""
from ocflib.printing.quota import get_schema


if __name__ == '__main__':
    print(get_schema())
