#!/usr/bin/env python3
"""Add a test refund."""
import getpass
import random
import string
from datetime import datetime

from ocflib.printing.quota import add_refund
from ocflib.printing.quota import get_connection
from ocflib.printing.quota import Refund


if __name__ == '__main__':
    user = 'ocfprinting'
    password = getpass.getpass('{} password: '.format(user))
    with get_connection(user=user, password=password) as c:
        add_refund(
            c,
            Refund(
                user=input('user: '),
                time=datetime.now(),
                pages=int(input('pages: ')),
                staffer=getpass.getuser(),
                reason=''.join(
                    random.choice(string.ascii_letters) for _ in range(30)
                ),
            ),
        )
