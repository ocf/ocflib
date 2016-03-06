#!/usr/bin/env python3
"""Add a test job."""
import getpass
import random
import string
from datetime import datetime

from ocflib.printing.printers import PRINTERS
from ocflib.printing.quota import add_job
from ocflib.printing.quota import get_connection
from ocflib.printing.quota import Job


if __name__ == '__main__':
    user = 'ocfprinting'
    password = getpass.getpass('{} password: '.format(user))
    with get_connection(user=user, password=password) as c:
        add_job(
            c,
            Job(
                user=input('user: '),
                time=datetime.now(),
                pages=int(input('pages: ')),
                queue=random.choice(('single', 'double')),
                printer=random.choice(tuple(PRINTERS)),
                doc_name=''.join(
                    random.choice(string.ascii_letters) for _ in range(30)
                ),
                filesize=random.randint(0, 2**28),
            ),
        )
