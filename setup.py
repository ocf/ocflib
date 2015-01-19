from setuptools import setup, find_packages

VERSION = 5

setup(
    name='ocflib',
    version=VERSION,
    author="Open Computing Facility",
    author_email='help@ocf.berkeley.edu',
    description="libraries for account and server management",
    url='https://www.ocf.berkeley.edu',
    packages=find_packages(),
    install_requires=(
        'paramiko',
        'cracklib',
        'pexpect',
        'dnspython3'
    )
)
