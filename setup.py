from setuptools import find_packages, setup

try:
    with open('.version') as f:
        VERSION = f.readline().strip()
except IOError:
    VERSION = '0.1a'

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
        'dnspython',
        'jinja2',
        'ldap3',
        'pexpect',
        'pycryptodome',
        'pygithub',
        'pymysql<0.10.0',
        'pysnmp',
        'pyyaml',
        'redis',
        'requests<2.25',  # temporarily downgraded due to pygithub incompat
        'sqlalchemy',
    ),
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
