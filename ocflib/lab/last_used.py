import ocflib.lab.stats

def make_fqdn(hostname):
    """Argparse custom type that appends ".ocf.berkeley.edu" to short hostnames."""
    if '.' not in hostname:
        return hostname + '.ocf.berkeley.edu'
    else:
        return hostname

def build_query(host):
    """Builds the MySQL query string with the given conditions."""
    query = 'SELECT * FROM `session`'
    query_args = []

    query_conditions = []
    query_conditions.append('`host` = %s')
    query_args.append(make_fqdn(host))
    
    query += ' WHERE ' + ' AND '.join(query_conditions)
    query += ' ORDER BY `start` DESC LIMIT 1'
    # we can't have another user start before current user ends so here we order by start

    return (query, query_args)

def last_used(desktop_host):
    try:
        with open('/etc/ocfstats-ro.passwd', 'r') as fin:
            password = fin.read().strip()
    except FileNotFoundError:
        return {"err": 'Could not find the file for ocfstats credentials. Are you running this on supernova?'}
    with ocflib.lab.stats.get_connection(user='ocfstats-ro',
                                         password=password) as c:
        query = build_query(desktop_host)
        c.execute(*query)
        return c.fetchone()