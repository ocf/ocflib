ocflib
======
[![Build Status](https://jenkins.ocf.berkeley.edu/buildStatus/icon?job=ocflib-test)](https://jenkins.ocf.berkeley.edu/view/ocflib-deploy/)
[![Coverage Status](https://coveralls.io/repos/ocf/ocflib/badge.svg?branch=master&service=github)](https://coveralls.io/github/ocf/ocflib?branch=HEAD)
[![PyPI version](https://badge.fury.io/py/ocflib.svg)](https://pypi.python.org/pypi/ocflib)

ocflib is a Python library for working with [Open Computing Facility][ocf]
services (in particular, accounts and server management).

The library targets Python 3.2 and 3.4 (the versions available in Debian wheezy
and jessie). Python 2.7 compatibility is a plus but not required or tested.

The goal of the library is to make it easier to re-use OCF python code. In the
past, code was split between approve, atool, create, chpass, sorry, signat,
etc., which made it difficult to do things like share common password
requirements.

## What belongs here

In general, code which can be re-used should be here, but standalone
applications or binaries shouldn't. For example, [atool][atool] uses ocflib
code to change passwords and create accounts, but the Django web app doesn't
belong here.

## Using on OCF

ocflib is installed by [Puppet][puppet] on the OCF, so you can simply do things
like `import ocflib.constants` from the system python3 installation. We *don't*
install it to python2 site-packages.

We build [a Debian package][debian-pkg] which is installed by Puppet. We also
publish new versions to [PyPI][pypi], which is useful because it allows easy
installation into virtualenvs.

## Testing changes

The easiest way to test changes to ocflib is to create a virtualenv and install
ocflib in development mode:

    virtualenv -p $(which python3) ~/venv/ocflib
    . ~/venv/ocflib/bin/activate
    pip install -r requirements-dev.txt
    pip install -e .

Now, if you import something from ocflib, you'll be using the version from your
working copy.

### Testing and linting

We use pytest to test our code, and flake8 to lint it. You should run `make
check` before pushing to run both.

The `tests` directory contains automated tests which you're encouraged to add
to (and not break). The `tests-manual` directory contains scripts intended for
testing.

#### Testing in a sandbox

Ideally, you should test your changes in a clean virtualenv (not the one you
develop in). To do this, just run `make tox-pyenv`. This will take a few
minutes as it downloads and compiles Python 3.2 and 3.4, creates virtualenvs
for both, then installs ocflib and runs the tests inside of them.

Normally, it is sufficient to just run `make check` from your development
environment, then push your changes. [Jenkins][jenkins] will run the tests in
the sandbox and catch any unexpected failures.

## Deploying changes

Deploying changes involves:

* Running tests and linters
* Pushing a new version to [PyPI][pypi]
* Building a Debian package
* Pushing the Debian package to our internal [apt][apt]

[Jenkins][jenkins] will automatically perform all of these steps for you on
every push, including automatically generating a new version number. As long as
`make tox-pyenv` passes, your code will be automatically deployed. You can
monitor the progress of your deploy [here][jenkins].

[ocf]: https://www.ocf.berkeley.edu/
[atool]: https://github.com/ocf/atool/
[puppet]: https://github.com/ocf/puppet/
[pypi]: https://pypi.python.org/pypi/ocflib
[apt]: http://apt.ocf.berkeley.edu/
[jenkins]: https://jenkins.ocf.berkeley.edu/view/ocflib-deploy/
[debian-pkg]: http://apt.ocf.berkeley.edu/pool/main/o/ocflib/
