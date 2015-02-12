# ocf ldap
OCF_LDAP = 'ldap.ocf.berkeley.edu'
OCF_LDAP_URL = 'ldaps://' + OCF_LDAP
OCF_LDAP_PEOPLE = 'ou=People,dc=OCF,dc=Berkeley,dc=EDU'
OCF_LDAP_HOSTS = 'ou=Hosts,dc=OCF,dc=Berkeley,dc=EDU'

OCF_KRB_REALM = 'OCF.BERKELEY.EDU'

OCF_MAIL_HOST = 'anthrax.ocf.berkeley.edu'
OCF_MAIL_PORT = 25

# university ldap
UCB_LDAP = 'ldap.berkeley.edu'
UCB_LDAP_URL = 'ldaps://' + UCB_LDAP
UCB_LDAP_PEOPLE = 'ou=People,dc=Berkeley,dc=EDU'

# calnet / cas
CAS_URL = 'https://auth.berkeley.edu/cas/'

# paths
KADMIN_PATH = '/usr/sbin/kadmin'
SENDMAIL_PATH = '/usr/sbin/sendmail'

QUEUED_ACCOUNTS_PATH = '/opt/create/public/approved.users'
CREATE_LOG_PATH = '/opt/create/public/approved.log'
CREATE_PUBKEY_PATH = '/opt/create/public/public_pass.pem'

VHOST_DB_URL = 'https://www.ocf.berkeley.edu/~staff/vhost.conf'

# mail
MAIL_ROOT = "root@ocf.berkeley.edu"
MAIL_FROM = "Open Computing Facility <help@ocf.berkeley.edu>"

MAIL_SIGNATURE = """Thanks for flying OCF,
The friendly staff of 6A Hearst Gym

=========
The Open Computing Facility is an all-volunteer, student-run service
group providing free printing, web hosting, disk space, and Unix shell
accounts.

OCF volunteers hold weekly staff hours to provide support:
https://ocf.io/staff-hours

Need help connecting to the OCF?
https://ocf.io/ssh

Need to reset your account password?
https://ocf.io/password"""

# don't bother listing accounts starting with 'ocf' here;
# those are always reserved
RESERVED_USERNAMES = [
    'abuse',
    'accounts',
    'admin',
    'announce',
    'approve',
    'archive',
    'arpwatch',
    'atool',
    'audit',
    'avahi',
    'backup',
    'bin',
    'bind',
    'board',
    'bod',
    'boinc',
    'clamav',
    'colord',
    'create',
    'cricket',
    'csgo',
    'daemon',
    'dca',
    'debmirror',
    'deforestation',
    'devnull',
    'donations',
    'dovecot',
    'dump',
    'dumper',
    'epidemic',
    'games',
    'geoclue',
    'gm',
    'gnats',
    'groups',
    'help',
    'hostmaster',
    'irc',
    'jabber',
    'libuuid',
    'lightdm',
    'list',
    'logjam',
    'lp',
    'mail',
    'mailinx',
    'mailman',
    'man',
    'manager',
    'messagebus',
    'minecraft',
    'mirrors',
    'mon',
    'munin',
    'mysql',
    'nagios',
    'nessus',
    'netsplit',
    'news',
    'nobody',
    'noc',
    'nogroup',
    'nomail',
    'nslcd',
    'ntp',
    'officers',
    'openldap',
    'opersquad',
    'paper',
    'pimp',
    'polw',
    'postfix',
    'postgres',
    'postgrey',
    'postmaster',
    'procmail',
    'projects',
    'proxy',
    'pulse',
    'puppet',
    'rancid',
    'root',
    'rt',
    'saned',
    'secretary',
    'security',
    'sexy',
    'sm',
    'spamd',
    'srcds',
    'sshd',
    'ssl',
    'staff',
    'statd',
    'steam',
    'sync',
    'sys',
    'systemd',
    'test',
    'testsmcc',
    'todo',
    'treasurer',
    'unscd',
    'usbmux',
    'user',
    'uucp',
    'vhost',
    'webmaster',
    'wheel',
    'www',
    'zabbix',
]
