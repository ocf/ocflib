"""Some utilities for shelling out and do kerberos stuff.
This should be considered temporary and find a non-shell out solution for our happiness"""
import json
import subprocess

# Initiates a kerberos ticket for current user
# Returns True when a new ticket is created via kinit so that we destroy it afterwards
# Raises OSError is kinit screwed up


def kerberos_init(username):
    klist = subprocess.run(['sudo', '-u', username, 'klist', '--json'], stdout=subprocess.PIPE)
    if klist.returncode == 0:
        cache_info = json.loads(klist.stdout.decode())
        if cache_info.get('principal') == '{}/admin@OCF.BERKELEY.EDU'.format(username):
            return False
    if (subprocess.call(['kinit', '{}/admin'.format(username)]) != 0):
        # Or some other kinds of Exception
        raise OSError('Kinit failed.')
    else:
        return True


def kerberos_destroy():
    return subprocess.call(['kdestroy'])
