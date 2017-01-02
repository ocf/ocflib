# ocf ldap
OCF_LDAP = 'ldap.ocf.berkeley.edu'
OCF_LDAP_URL = 'ldaps://' + OCF_LDAP
OCF_LDAP_PEOPLE = 'ou=People,dc=OCF,dc=Berkeley,dc=EDU'
OCF_LDAP_HOSTS = 'ou=Hosts,dc=OCF,dc=Berkeley,dc=EDU'

OCF_KRB_REALM = 'OCF.BERKELEY.EDU'

OCF_MAIL_HOST = 'anthrax.ocf.berkeley.edu'
OCF_MAIL_PORT = 25

SORRIED_SHELL = '/opt/share/utils/bin/sorried'

# university ldap
UCB_LDAP = 'ldap.berkeley.edu'
UCB_LDAP_URL = 'ldaps://' + UCB_LDAP
UCB_LDAP_PEOPLE = 'ou=People,dc=Berkeley,dc=EDU'

# calnet / cas
CAS_URL = 'https://auth.berkeley.edu/cas/'

# paths
KADMIN_PATH = '/usr/bin/kadmin'
SENDMAIL_PATH = '/usr/sbin/sendmail'

QUEUED_ACCOUNTS_PATH = '/opt/create/public/approved.users'
CREATE_LOG_PATH = '/opt/create/public/approved.log'
CREATE_PUBKEY_PATH = '/opt/create/public/public_pass.pem'

VHOST_DB_PATH = '/home/s/st/staff/vhost/vhost.conf'
VHOST_DB_URL = 'https://www.ocf.berkeley.edu/~staff/vhost.conf'

# mail
MAIL_ROOT = 'root@ocf.berkeley.edu'
MAIL_FROM = 'Open Computing Facility <help@ocf.berkeley.edu>'

MAIL_SIGNATURE = """Thanks for flying OCF,
The friendly staff of 171 MLK Student Union

=========
The Open Computing Facility is an all-volunteer, student-run service
group providing free printing, web hosting, disk space, and Unix shell
accounts.

We love free & open-source software. Sound like you? Get involved!
https://ocf.io/staff

OCF volunteers hold weekly staff hours to provide support:
https://ocf.io/staff-hours

Need help connecting to the OCF?
https://ocf.io/ssh

Need to reset your account password?
https://ocf.io/password"""

# words not allowed in usernames
BAD_WORDS = frozenset(('fuck', 'shit', 'cunt', 'bitch', 'dick'))
RESTRICTED_WORDS = frozenset(('ocf', 'ucb', 'cal', 'berkeley', 'university'))

# don't bother listing accounts starting with 'ocf' here;
# those are always reserved
RESERVED_USERNAMES = frozenset((
    'Debian-exim',
    'Debian-gdm',
    '_graphite',
    'about',
    'abuse',
    'account',
    'accounts',
    'admin',
    'administrator',
    'alums',
    'announce',
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
    'beauracracy',
    'beaurocracy',
    'bin',
    'bind',
    'board',
    'bod',
    'boinc',
    'bureacrucy',
    'bureaucracy',
    'cabinet',
    'callinkapi',
    'chronos',
    'clamav',
    'colord',
    'contact',
    'control',
    'create',
    'cricket',
    'csgo',
    'daemon',
    'davfs2',
    'dca',
    'debian-security-support',
    'debian-spamd',
    'debian-transmission',
    'debmirror',
    'deforestation',
    'devnull',
    'dnsmasq',
    'docs',
    'donations',
    'dovecot',
    'dump',
    'dumper',
    'elasticsearch',
    'email',
    'epidemic',
    'faq',
    'ftp',
    'games',
    'geoclue',
    'gh',
    'github',
    'gitlab-runner',
    'gm',
    'gnats',
    'groups',
    'hello',
    'help',
    'hiring',
    'host',
    'hosting',
    'hostmaster',
    'hours',
    'hplip',
    'https',
    'info',
    'iodine',
    'irc',
    'jabber',
    'jenkins',
    'jenkins-deploy',
    'jenkins-slave',
    'join',
    'knhosss',
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
    'memcache',
    'mesos',
    'messagebus',
    'minecraft',
    'mirrors',
    'mis',
    'mlk',
    'mon',
    'mongodb',
    'move',
    'mumble-server',
    'munin',
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
    'noreply',
    'nslcd',
    'ntp',
    'officers',
    'oident',
    'opencf',
    'opencomp',
    'openldap',
    'operations',
    'opersquad',
    'opstaff',
    'pagefault',
    'paper',
    'papercut',
    'password',
    'pimp',
    'polw',
    'postfix',
    'postgres',
    'postgrey',
    'postmaster',
    'print',
    'printing',
    'procmail',
    'projects',
    'prosody',
    'proxy',
    'pulse',
    'puppet',
    'rabbitmq',
    'rancid',
    'redis',
    'register',
    'requesttracker',
    'root',
    'rt',
    'rtkit',
    'sales',
    'saned',
    'secretary',
    'security',
    'senate-resolution',
    'servers',
    'sexy',
    'shellinabox',
    'shorturl',
    'sm',
    'snmp',
    'spamass-milter',
    'spamd',
    'srcds',
    'ssh',
    'sshd',
    'ssl',
    'ssladmin',
    'ssladministrator',
    'sslwebmaster',
    'staff',
    'staffhours',
    'statd',
    'stats',
    'status',
    'steam',
    'stf-cost-breakdown',
    'support',
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
    'todo',
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
    'waf',
    'web',
    'webmaster',
    'wheel',
    'wiki',
    'wordpress',
    'www',
    'www-data',
    'yacy',
    'zabbix',
    'zandronum',
    'znc',
    'zookeeper',

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

CREATE_PUBLIC_KEY = '''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3xG2dczz2y+qc0AgTZ1L
Jrun4RbcMf7z7AFqPqIQrtbuJprg6EQPHd2EDjMt9rJm929tTatjLu7TcNisq9lW
AMU85c1nM6l4ce58mIXGzaB5yCGP0Qfcos5o00xJOmRVmxZGB5D2Jli+JbmEHPpo
KbvI3DuNLNbS+MxXawudEDVj0xA86Iv8biHqq//xMD+SicOzN4ZrjKarT9MdQYL+
JDNjiYba1ZiNLiqXeLGS2IVYAd88etX+V5gxAvl0bGHzgeHodutxUf46QCg7cmvm
5lQsbiYUABiEsE1OejSEfb+7mtuhxu+MeVXCYr341axa0IHorj4qURxKOi/CTn5f
zwIDAQAB
-----END PUBLIC KEY-----'''
