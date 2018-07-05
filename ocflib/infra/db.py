import pymysql


def get_connection(user,
                   password,
                   db,
                   host='mysql.ocf.berkeley.edu',
                   cursorclass=pymysql.cursors.DictCursor,
                   charset='utf8mb4',
                   autocommit=True,
                   **kwargs):
    """Returns a context-manager aware connection to MariaDB, with sensible defaults.

    While this function can be called directly, there are partial function
    in some ocflib modules that may be better suited for particular tasks."""

    return pymysql.connect(
        user=user,
        password=password,
        db=db,
        host=host,
        cursorclass=cursorclass,
        charset=charset,
        autocommit=autocommit,
        **kwargs
    )


def namedtuple_to_query(query, nt):
    """Return a filled-out query and arguments.

    The return value can be exploded and passed directly into execute.

    >>> query = 'INSERT INTO jobs ({}) VALUES ({});'
    >>> namedtuple_to_query(query, job)
    ('INSERT INTO jobs (`user`, `pages`) VALUES (%s, %s)', ('ckuehl', 42))
    """
    return (
        query.format(
            ', '.join('`{}`'.format(column) for column in nt._fields),
            ', '.join('%s' for _ in nt._fields),
        ),
        tuple(getattr(nt, column) for column in nt._fields),
    )
