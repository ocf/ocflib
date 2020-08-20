import difflib
import pwd
import string
import sys

import cracklib

import ocflib.misc.mail

RESERVED_USERNAMES = frozenset((
    # Misc
    'Debian-exim',
    'Debian-gdm',
    '_graphite',
    'about',
    'account',
    'accounts',
    'admin',
    'administrator',
    'apphost',
    'applicationhost',
    'approve',
    'apt-dater',
    'archive',
    'arpwatch',
    'atool',
    'audit',
    'avahi',
    'backup',
    'badgr',
    'bin',
    'bind',
    'bjb',
    'board',
    'boinc',
    'bullseye',
    'buster',
    'buy',
    'buysheet',
    'cabinet',
    'callinkapi',
    'ceph',
    'chronos',
    'clamav',
    'codimd',
    'colord',
    'contact',
    'control',
    'create',
    'cricket',
    'csgo',
    'daemon',
    'datathon',
    'davfs2',
    'dca',
    'debian-security-support',
    'debian-spamd',
    'debian-transmission',
    'debmirror',
    'decalform',
    'deforestation',
    'directors',
    'discord',
    'dns',
    'dnsmasq',
    'docs',
    'donate',
    'donations',
    'dovecot',
    'dump',
    'dumper',
    'elasticsearch',
    'element',
    'email',
    'epidemic',
    'facebook',
    'families',
    'faq',
    'ftp',
    'games',
    'geoclue',
    'getinvolved',
    'gettinginvolved',
    'gh',
    'github',
    'gitlab-runner',
    'gnats',
    'groups',
    'guest',
    'haproxy',
    'hello',
    'hiring',
    'host',
    'hosting',
    'hours',
    'hpc',
    'hplip',
    'https',
    'icinga',
    'info',
    'infra',
    'internal',
    'internals',
    'iodine',
    'irc',
    'jabber',
    'jenkins-deploy',
    'jenkins-slave',
    'job',
    'join',
    'joinfamily',
    'keyserver',
    'lab',
    'lets-encrypt',
    'libuuid',
    'libvirt-qemu',
    'lightdm',
    'list',
    'logjam',
    'lp',
    'mail',
    'mailinx',
    'mailman',
    'man',
    'manager',
    'marketing',
    'mastodon',
    'matrix',
    'memcache',
    'mesos',
    'messagebus',
    'minecraft',
    'minutes',
    'mis',
    'mlk',
    'mongodb',
    'move',
    'mumble-server',
    'mysql',
    'nagios',
    'nessus',
    'netsplit',
    'news',
    'nginx',
    'nobody',
    'noc',
    'nogroup',
    'nomail',
    'nonexist',
    'nonexistent',
    'noreply',
    'nslcd',
    'ntp',
    'oident',
    'opencf',
    'opencomp',
    'openldap',
    'opersquad',
    'pagefault',
    'paper',
    'papercut',
    'password',
    'pgp',
    'polw',
    'postfix',
    'postgres',
    'postgrey',
    'print',
    'printer',
    'printers',
    'printerlog',
    'printing',
    'procmail',
    'production',
    'prometheus',
    'prosody',
    'proxy',
    'pulse',
    'rabbitmq',
    'redis',
    'register',
    'requesttracker',
    'reserve',
    'rtkit',
    'sales',
    'saned',
    'sdocs',
    'secretary',
    'senate-resolution',
    'servers',
    'sexy',
    'shellinabox',
    'shirts',
    'shorturl',
    'signin',
    'sks',
    'slack',
    'snmp',
    'socialrules',
    'spamass-milter',
    'spamd',
    'srcds',
    'ssh',
    'sshd',
    'ssl',
    'ssladmin',
    'ssladministrator',
    'sslwebmaster',
    'staffhours',
    'startertasks',
    'statd',
    'stats',
    'status',
    'steam',
    'stf-cost-breakdown',
    'stretch',
    'support',
    'survey',
    'sync',
    'sys',
    'sysadmin',
    'systemd',
    'systemd-bus-proxy',
    'systemd-network',
    'systemd-resolve',
    'systemd-timesync',
    'test',
    'testsmcc',
    'tftp',
    'treasurer',
    'tw',
    'twitter',
    'university',
    'unscd',
    'usbmux',
    'usenet',
    'user',
    'uucp',
    'uuidd',
    'vde2-net',
    'vhost',
    'vnc',
    'web',
    'webhost',
    'webhosting',
    'webmaster',
    'wiki',
    'wordpress',
    'www',
    'www-data',
    'xkcd',
    'yacy',
    'youtube',
    'zabbix',
    'zandronum',
    'znc',
    'zookeeper',
    'zoom',

    # RT queues
    'bod',
    'beauracracy',
    'beaurocracy',
    'bureacrucy',
    'bureaucracy',
    'devnull',
    'help',
    'hostmaster',
    'lending',
    'operations',
    'projects',
    'security',
    'techtalks',
    'todo',

    # Mailing lists, aliases, and legacy mailing lists
    'abuse',
    'alums',
    'alumnus',
    'announce',
    'decal',
    'decal-announce',
    'extcomm',
    'gm',
    'jenkins',
    'joinstaff',
    'mirrors',
    'manager',
    'managers',
    'mon',
    'munin',
    'officers',
    'opstaff',
    'pimp',
    'postmaster',
    'projects',
    'puppet',
    'rancid',
    'root',
    'rt',
    'rt-ops',
    'sks',
    'sm',
    'staff',
    'wheel',

    # Usernames of some former staffers whose accounts were later lost
    'adamj',     # Adam Richter (former account, still has User_Info)
    'anniem',    # Ann Matsubara
    'appel',     # Shannon Appel
    'blojo',     # Jon Blow
    'chamm',
    'chaynges',  # Cynthia Haynes
    'cjain',     # Chris Jain
    'dpassage',  # David Paschich
    'euphrasi',
    'evil',
    'glass',     # Adam Glass
    'ianb',
    'karat',     # Eddy Karat
    'kinshuk',   # Kinshuk Govil
    'kit',
    'marko',     # Mark Nolte
    'moray',
    'nweaver',   # Nicholas Weaver
    'pbrown',
    'reiser',    # Hans Reiser
    'rgm',       # Rob Menke
    'shannona',  # Shannon Appel (former account, still has User_Info)
    'steveg',
    'welch',     # Sean Welch
    'yukai',
))


def validate_username(username, check_exists=False):
    """Validate a username, raising a descriptive exception if problems are
    encountered."""

    if username_reserved(username):
        raise ValueError('Username is reserved.')

    if not 3 <= len(username) <= 16:
        raise ValueError('Username must be between 3 and 16 characters.')

    if not all(c.islower() for c in username):
        raise ValueError('Username must be all lowercase letters.')

    if check_exists and not user_exists(username):
        raise ValueError('Username does not exist.')


def validate_password(username, password, strength_check=True):
    """Validate a password, raising a descriptive exception if problems are
    encountered. Optionally checks password strength."""

    if strength_check:
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters.')

        s = difflib.SequenceMatcher()
        s.set_seqs(password, username)

        if s.ratio() > 0.6:
            raise ValueError('Password is too similar to username.')

        try:
            cracklib.VeryFascistCheck(password)
        except ValueError as e:
            raise ValueError('Password problem: {}.'.format(e))

    # sanity check; note we don't use string.whitespace since we don't want
    # tabs or newlines
    allowed = string.digits + string.ascii_letters + string.punctuation + ' '

    if not all(c in allowed for c in password):
        raise ValueError('Password contains forbidden characters.')


# TODO: we have two implementations of this (one here, one in search).
# one should be removed.
def user_exists(username):
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False
    else:
        return True


def username_reserved(username):
    if username.startswith('ocf'):
        return True

    if username in RESERVED_USERNAMES:
        return True

    # sanity check: make sure no local users share the username
    with open('/etc/passwd') as f:
        if any(line.startswith(username + ':') for line in f):
            print(
                'WARNING: Username {} rejected based on /etc/passwd!'
                .format(username),
                file=sys.stderr)
            ocflib.misc.mail.send_problem_report(
                """Username {} rejected based on /etc/passwd. It should be \
added to RESERVED_USERNAMES for consistency across \
servers!""".format(username))
            return True

    return False
