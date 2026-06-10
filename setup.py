from setuptools import find_packages
from setuptools import setup

try:
    with open('.version') as f:
        VERSION = f.readline().strip()
except IOError:
    VERSION = '2026.06.09'

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
        'attrs',
        'zxcvbn',
        'dnspython',
        'jinja2',
        'ldap3',
        'passlib',
        'pexpect',
        'pycryptodome',
        'pygithub',
        'pymysql',
        'puresnmp',
        'pyyaml',
        'redis',
        'requests',
        'sqlalchemy>=2.0',
    ),
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
