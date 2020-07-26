import re
import uuid
from collections import namedtuple
from datetime import date
from textwrap import dedent

from ocflib.account.search import user_attrs
from ocflib.account.search import user_attrs_ucb
from ocflib.infra.github import GitRepo
from ocflib.infra.rt import rt_connection
from ocflib.infra.rt import RtTicket
from ocflib.misc.mail import send_problem_report

VHOST_DB_PATH = '/etc/ocf/vhost.conf'
GITHUB_VHOST_REPO = 'ocf/etc'
GITHUB_VHOST_WEB_PATH = 'configs/vhost.conf'


def get_vhost_db(remote=False):
    """Returns lines from the vhost config file. If remote is True, fetches it
    from GitHub."""
    if remote:
        vhosts = GitRepo(GITHUB_VHOST_REPO).get_file(GITHUB_VHOST_WEB_PATH)
        return vhosts.splitlines()
    else:
        with open(VHOST_DB_PATH) as f:
            return f.read().splitlines()


def pr_new_vhost(credentials, username, aliases=None, docroot=None, flags='', rt_ticket=''):
    """
    Creates a GitHub pull request on the vhosts file to add a new vhost
    """
    if not aliases:
        aliases = '-'
    else:
        aliases = ','.join(aliases)

    if not docroot:
        docroot = '-'

    repo = GitRepo(GITHUB_VHOST_REPO, credentials=credentials)
    vhosts_lines = get_vhost_db(remote=True)

    # skip the initial comment block
    idx = 0
    while idx < len(vhosts_lines):
        if not vhosts_lines[idx].startswith('#'):
            break
        idx += 1

    vhosts_lines.insert(idx, dedent("""
        # added {date} web {rt_ticket}
        {username} {aliases} {docroot} {flags}""").format(
        date=date.today(),
        rt_ticket='rt#{}'.format(rt_ticket) if rt_ticket else '',
        username=username,
        aliases=aliases,
        docroot=docroot,
        flags=flags,
    ))

    new_vhosts_file = '\n'.join(vhosts_lines) + '\n'  # newline at eof
    new_branch_name = '{rt_ticket}{id}'.format(
        rt_ticket='rt#{}-'.format(rt_ticket) if rt_ticket else '',
        id=uuid.uuid4().hex
    )

    repo.modify_and_branch(
        'master',
        new_branch_name,
        'rt#{rt_ticket}: Add vhost for {username}'.format(
            rt_ticket=rt_ticket,
            username=username,
        ),
        GITHUB_VHOST_WEB_PATH,
        new_vhosts_file,
    )

    pull_body = dedent("""
        Submitted from ocflib on {date}

        Username: {username}
        Aliases: {aliases}
        Document root: {docroot}
        Flags: {flags}

        Associated RT Ticket: rt#{rt_ticket}
        https://ocf.io/rt/{rt_ticket}
        """).format(
        date=date.today(),
        rt_ticket=rt_ticket,
        username=username,
        aliases=aliases,
        docroot=docroot,
        flags=flags,
    )

    repo.github.create_pull(
        title='rt#{rt_ticket}: Add vhost for {username}'.format(
            rt_ticket=rt_ticket,
            username=username,
        ),
        body=pull_body,
        base='master',
        head=new_branch_name,
    )


def get_vhosts():
    """Returns a list of virtual hosts in convenient format.

    >>> get_vhosts()
    ...
    {
        'bpreview.berkeley.edu': {
            'username': 'bpr',
            'aliases': ['bpr.berkeley.edu'],
            'docroot': '/',
            'flags': [],
        }
    }
    ...
    """
    def fully_qualify(host):
        """Fully qualifies a hostname (by appending .berkeley.edu) if it's not
        already fully-qualified."""
        return host if '.' in host else host + '.berkeley.edu'

    vhosts = {}

    for line in get_vhost_db():
        if not line or line.startswith('#'):
            continue

        fields = line.split(' ')

        if len(fields) < 5:
            flags = []
        else:
            flags = re.match(r'\[(.*)\]$', fields[4]).group(1).split(',')

        username, host, aliases, docroot = fields[:4]

        if aliases != '-':
            aliases = list(map(fully_qualify, aliases.split(',')))
        else:
            aliases = []

        vhosts[fully_qualify(username if host == '-' else host)] = {
            'username': username,
            'aliases': aliases,
            'docroot': '/' if docroot == '-' else docroot,
            'flags': flags,
        }

    return vhosts


def has_vhost(user):
    """Returns whether or not a virtual host is already configured for
    the given user."""
    return any(vhost['username'] == user for vhost in get_vhosts().values())


def eligible_for_vhost(user):
    """Returns whether a user account is eligible for virtual hosting.

    Currently, group accounts, faculty, and staff are eligible for virtual
    hosting.
    """
    attrs = user_attrs(user)
    if 'callinkOid' in attrs:
        return True
    elif 'calnetUid' in attrs:
        attrs_ucb = user_attrs_ucb(attrs['calnetUid'])
        # TODO: Uncomment when we get a privileged LDAP bind.
        if attrs_ucb:  # and 'EMPLOYEE-TYPE-ACADEMIC' in attrs_ucb['berkeleyEduAffiliations']:
            return True

    return False


def get_tasks(celery_app, credentials=None):
    """Return Celery tasks instantiated against the provided instance."""

    @celery_app.task
    def create_new_vhost(request):
        try:
            conn = rt_connection(credentials['rt'].username, credentials['rt'].password)
            ticket_number = RtTicket.create(
                conn,
                'hostmaster',
                request.requestor,
                request.subject,
                request.message,
            )

            pr_new_vhost(
                credentials['github'],
                request.username,
                request.aliases,
                request.docroot,
                request.flags,
                ticket_number,
            )
            return True
        except Exception as e:
            send_problem_report(str(e))
            return False

    return _VirtualHostTasks(
        create_new_vhost=create_new_vhost,
    )


_VirtualHostTasks = namedtuple('VirtualHostTasks', [
    'create_new_vhost',
])


class NewVirtualHostRequest(namedtuple('NewVirtualHostRequest', [
    'username',
    'requestor',
    'subdomain',
    'aliases',
    'docroot',
    'flags',
    'rt_ticket',
    'subject',
    'message',
])):
    """Request for account creation.

    :param username: str
    :param requestor: str
    :param subdomain: str
    :param aliases: str or None
    :param docroot: str or None
    :param flags: str or None
    :param rt_ticket: str or None
    :param subject: str or None
    :param message: str or None
    """
