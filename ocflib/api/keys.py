from binascii import hexlify
from os import urandom

import pymsql


"""Constants
Changes here should be reflected in the corresponding keys.sql file if
necessary
"""
KEY_LENGTH = 32


def _generate_key(length=KEY_LENGTH):
    """Return a random `length` string to be used as a key
    """
    return hexlify(urandom(length)).decode()


def add_key(cursor, user):
    """Add a key for a user into the database

    Args:
        cursor (pymysql.cursors.Cursor): database cursor
        user (str): user to add the key for

    Returns:
        None
    """
    key = _generate_key()
    cursor.execute(
        'INSERT INTO `keys`'
        '(`key`, `user`)'
        'VALUES (%s, %s, %s)',
        (key, user)
    )


def get_key(cursor, user):
    """Get the key corresponding to the user in the db

    Args:
        cursor (pymysql.cursors.Cursor): database cursor
        user (str): user to get the key for

    Returns:
        (str) the user's key
    """
    cursor.execute(
        'SELECT `key`'
        'FROM `keys`'
        'WHERE `user` LIKE %s',
        (user,),
    )
    query_result = cursor.fetchone()
    try:
        return query_result['key']
    except (KeyError, TypeError):
        # query_result is None or doesn't have a key
        return ""
        
    return cursor.fetchone()['key']

def get_connection(user, password, db='keys', **kwargs):
    """Return a connection to MySQL."""
    return pymysql.connect(
        user=user,
        password=password,
        db=db,
        host='mysql.ocf.berkeley.edu',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        **dict({'autocommit': True}, **kwargs)
    )
