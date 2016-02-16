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
    packages=find_packages(),
    package_data={
        'ocflib.account': ['rc/*'],
    },
    install_requires=(
        'cached_property',
        'colorama',
        'cracklib',
        'dnspython3',
        'ldap3',
        'paramiko',
        # pexpect 3.3 (currently the latest) breaks with multiprocessing/celery
        # https://github.com/pexpect/pexpect/issues/86
        'pexpect<3.2.999',
        'pycrypto',
        # TODO: Remove this version restriction after upgrade to jessie
        #   Currently pymysql breaks with Python 3.2.x (rt#4267)
        'pymysql<0.6.7',
        'pysnmp',
        'pyyaml',
        'redis',
        'requests',
        'sqlalchemy',
    ),
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
