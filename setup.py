from setuptools import find_packages
from setuptools import setup

try:
    with open('.version') as f:
        VERSION = f.readline().strip()
except IOError:
    VERSION = 'unknown'

setup(
    name='ocflib',
    version=VERSION,
    author='Open Computing Facility',
    author_email='help@ocf.berkeley.edu',
    description='libraries for account and server management',
    url='https://www.ocf.berkeley.edu',
    packages=find_packages(exclude=('tests*',)),
    package_data={
        'ocflib.account': ['mail_templates/*'],
        'ocflib.printing': ['ocfprinting.schema'],
        'ocflib.vhost': ['ocfmail.schema'],
    },
    install_requires=(
        'cached_property',
        'cracklib',
        'dnspython',
        'jinja2',
        'ldap3',
        'paramiko',
        'pexpect',
        'pycrypto',
        'pymysql',
        # 4.3.3 adds a dependency on "pycryptodome" which conflicts with pycrypto
        'pysnmp<=4.3.2',
        'pyyaml',
        'redis',
        'requests',
        'sqlalchemy',
    ),
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
