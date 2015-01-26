ocflib
======
[![Build Status](https://travis-ci.org/ocf/ocflib.svg)](https://travis-ci.org/ocf/ocflib)
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

ocflib is published on [PyPI][pypi], and new versions are automatically
installed from there every time puppet runs.

## Testing changes

The easiest way to test changes to ocflib is to create a virtualenv and install
ocflib in development mode:

    virtualenv -p $(which python3) ~/venv/ocflib
    . ~/venv/ocflib/bin/activate
    python3 setup.py develop

Now, if you import something from ocflib, you'll be using the version from your
working copy.

### Testing and linting

We use flake8 to lint our code. You should run `make check` before pushing to
run the linter.

Currently, the `tests` directory contains a bunch of standalone executable
Python scripts for testing various parts of ocflib. These are useful by
themselves, and you're encouraged to maintain and add to them. Eventually we'd
like to replace them with automated tests (while keeping some which can't
easily be automated on a build server, such as password changing).

## Deploying changes

To deploy changes, we push a new update to PyPI. The easiest way to do this is
by executing `make release`, which will increment the version number, build a
source distribution and upload it. Note that you need to have permission to
push to PyPI. Make sure to commit and push the version number change after
releasing.

[ocf]: https://www.ocf.berkeley.edu/
[atool]: https://github.com/ocf/atool/
[puppet]: https://github.com/ocf/puppet/
[pypi]: https://pypi.python.org/pypi/ocflib
