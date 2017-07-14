#!/usr/bin/env python3
import getpass
import sys

from ocflib.vhost.mail import get_connection
from ocflib.vhost.mail import get_mail_vhosts


def main():
    user = 'ocfmail-ro'
    password = getpass.getpass('enter password for {}: '.format(user))

    with get_connection(user, password) as c:
        for vhost in get_mail_vhosts():
            print('{vhost.domain} ({vhost.user}):'.format(vhost=vhost))
            print('=' * 50)

            for addr in vhost.get_forwarding_addresses(c):
                print('    {}'.format(addr))

            print()


if __name__ == '__main__':
    sys.exit(main())
