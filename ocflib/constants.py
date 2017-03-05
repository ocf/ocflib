"""Constants.

PLEASE DO NOT ADD NEW CONSTANTS TO THIS MODULE.
THIS MODULE WAS A BAD IDEA AND I AM SORRY.

Instead, constants should live in a specific module related to their purpose.
For example, LDAP-related constants should be in `ocflib.infra.ldap`.

Ideally we should one day move everything out of this module.
"""
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
