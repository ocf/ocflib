from setuptools import find_packages
from setuptools import setup

with open('.version') as f:
    VERSION = f.readline().strip()

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
        'colorama',
        'cracklib',
        'dnspython3',
        'ldap3',
        'paramiko',
        # pexpect 3.3 (currently the latest) breaks with multiprocessing/celery
        # https://github.com/pexpect/pexpect/issues/86
        'pexpect<3.2.999',
        'pycrypto',
        'pymysql',
        'pysnmp',
        'pyyaml',
        'redis',
        'requests',
        'sqlalchemy',
    )
)
