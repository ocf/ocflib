import functools

from ocflib.infra import mysql


get_connection = functools.partial(
    mysql.get_connection,
    db='ocfshorturls',
    user='anonymous',
    password=None,
)
