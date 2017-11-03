ocflib
======
[![Build Status](https://jenkins.ocf.berkeley.edu/buildStatus/icon?job=ocflib/master)](https://jenkins.ocf.berkeley.edu/job/ocflib/job/master/)
[![Coverage Status](https://coveralls.io/repos/ocf/ocflib/badge.svg?branch=HEAD&service=github)](https://coveralls.io/github/ocf/ocflib?branch=HEAD)
[![Code Health](https://landscape.io/github/ocf/ocflib/master/landscape.svg?style=flat)](https://landscape.io/github/ocf/ocflib/master)
[![PyPI version](https://badge.fury.io/py/ocflib.svg)](https://pypi.python.org/pypi/ocflib)

ocflib is a Python library for working with [Open Computing Facility][ocf]
services (in particular, accounts and server management).

The library targets Python 3.4 and 3.5 (the versions available in Debian jessie
and stretch).

The goal of the library is to make it easier to re-use OCF python code. In the
past, code was split between approve, atool, create, chpass, sorry, signat,
etc., which made it difficult to do things like share common password
requirements.


## What belongs here

In general, code which can be re-used should be here, but standalone
applications or binaries shouldn't. For example, [ocfweb][ocfweb] uses ocflib
code to change passwords and create accounts, but the Django web app doesn't
belong here.


## Using on OCF

ocflib is installed by [Puppet][puppet] on the OCF, so you can simply do things
like `import ocflib.lab.stats` from the system python3 installation. We *don't*
install it to python2 site-packages.

We build [a Debian package][debian-pkg] which is installed by Puppet. We also
publish new versions to [PyPI][pypi], which is useful because it allows easy
installation into virtualenvs.


## Testing changes

The easiest way to test changes to ocflib is to create a virtualenv and install
ocflib in development mode:

    make venv
    . venv/bin/activate

Now, if you import something from ocflib, you'll be using the version from your
working copy.


### Testing and linting

We use pytest to test our code, and pre-commit to lint it. You should run `make
test` before pushing to run both.

The `tests` directory contains automated tests which you're encouraged to add
to (and not break). The `tests-manual` directory contains scripts intended for
testing.


#### Using pre-commit

We use [pre-commit][pre-commit] to lint our code before commiting. While some
of the rules might seem a little arbitrary, it helps keep the style consistent,
and ensure annoying things like trailing whitespace don't creep in.

You can simply run `make install-hooks` to install the necessary git hooks;
once installed, pre-commit will run every time you commit.

Alternatively, if you'd rather not install any hooks, you can simply use `make
test` as usual, which will also run the hooks.


## Deploying changes

Deploying changes involves:

* Running tests and linters
* Pushing a new version to [PyPI][pypi]
* Building a Debian package
* Pushing the Debian package to our internal [apt][apt]

[Jenkins][jenkins] will automatically perform all of these steps for you on
every push, including automatically generating a new version number. As long as
`make test` passes, your code will be automatically deployed. You can
monitor the progress of your deploy [here][jenkins].

[ocf]: https://www.ocf.berkeley.edu/
[ocfweb]: https://github.com/ocf/ocfweb/
[puppet]: https://github.com/ocf/puppet/
[pypi]: https://pypi.python.org/pypi/ocflib
[apt]: http://apt.ocf.berkeley.edu/
[jenkins]: https://jenkins.ocf.berkeley.edu/view/ocflib-deploy/
[debian-pkg]: http://apt.ocf.berkeley.edu/pool/main/p/python-ocflib/
[pre-commit]: http://pre-commit.com/
