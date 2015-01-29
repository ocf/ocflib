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

MAIL_FROM = "Open Computing Facility <help@ocf.berkeley.edu>"

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
    'gm',
    'gnats',
    'groups',
    'help',
    'hostmaster',
    'irc',
    'jabber',
    'libuuid',
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
    'mysql',
    'nagios',
    'nessus',
    'netsplit',
    'news',
    'nobody',
    'noc',
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
    'sshd',
    'ssl',
    'staff',
    'statd',
    'sync',
    'sys',
    'systemd',
    'test',
    'testsmcc',
    'todo',
    'treasurer',
    'usbmux',
    'user',
    'uucp',
    'webmaster',
    'wheel',
    'www',
    'zabbix'
]
