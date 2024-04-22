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
