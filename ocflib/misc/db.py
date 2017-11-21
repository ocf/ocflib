import pymysql


def get_connection(user,
                   password,
                   db,
                   host='mysql.ocf.berkeley.edu',
                   cursorclass=pymysql.cursors.DictCursor,
                   charset='utf8mb4',
                   autocommit=True,
                   **kwargs):
    return pymysql.connect(
        user=user,
        password=password,
        db=db,
        host=host,
        cursorclass=cursorclass,
        charset=charset,
        autocommit=autocommit
    )
