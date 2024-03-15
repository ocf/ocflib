# ocflib

[![Build Status](https://jenkins.ocf.berkeley.edu/buildStatus/icon?job=ocf/ocflib/master)](https://jenkins.ocf.berkeley.edu/job/ocf/job/ocflib/job/master)
[![Coverage Status](https://coveralls.io/repos/github/ocf/ocflib/badge.svg?branch=master)](https://coveralls.io/github/ocf/ocflib?branch=master)
[![PyPI version](https://badge.fury.io/py/ocflib.svg)](https://pypi.org/project/ocflib/)

ocflib is a Python library for working with [Open Computing Facility][ocf]
services (in particular, accounts and server management).

The library targets Python 3.5.3 and 3.7 (the versions available in Debian
stretch and buster).

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
like `import ocflib.lab.stats` from the system python3 installation. We _don't_
install it to python2 site-packages.

We build [a Debian package][debian-pkg] which is installed by Puppet. We also
publish new versions to [PyPI][pypi], which is useful because it allows easy
installation into virtualenvs.

## Note about lockfiles

This repository includes a `poetry.lock` file. Lockfiles are usually used to
ensure that the exact same versions of dependencies are installed across
different machines. However, as this is a library, we don't want to force
downstream users to use the exact same versions of dependencies as us, and
indeed, the lockfile is ignored when distributing. We still include it in the
repository to make it easier to develop, test, and debug ocflib.

## Installing locally

### For Testing Changes

Development of ocflib uses [Poetry](https://python-poetry.org/). The easiest way
to test changes to ocflib is to let Poetry manage the virtual environment for
you:

    poetry install
    poetry shell

Now, if you import something from ocflib, you'll be using the version from your
working copy.

### Testing and linting

We use pytest to test our code, and pre-commit to lint it. You should run
`make test` before pushing to run both.

The `tests` directory contains automated tests which you're encouraged to add to
(and not break). The `tests-manual` directory contains scripts intended for
testing.

#### Using pre-commit

We use [pre-commit][pre-commit] to lint our code before commiting. While some of
the rules might seem a little arbitrary, it helps keep the style consistent, and
ensure annoying things like trailing whitespace don't creep in.

You can simply run `make install-hooks` to install the necessary git hooks; once
installed, pre-commit will run every time you commit.

Alternatively, if you'd rather not install any hooks, you can simply use
`make test` as usual, which will also run the hooks.

### Troubleshooting: Cracklib Error

If you're trying to run make install-hooks on ocfweb (or related repos) and get
this error:

```
./_cracklib.c:40:10: fatal error: 'crack.h' file not found
  #include <crack.h>
           ^~~~~~~~~
  1 error generated.
```

The issue relates to the cracklib package not finding the necessary header files
to install. Make sure cracklib is installed on your machine
(https://github.com/cracklib/cracklib, if you're on Mac,
`brew install cracklib`).

## Deploying changes

Deploying changes involves:

- Running tests and linters
- Pushing a new version to [PyPI][pypi]
- Building a Debian package
- Pushing the Debian package to our internal [apt][apt]

[Jenkins][jenkins] will automatically perform all of these steps for you on
every push, including automatically generating a new version number. As long as
`make test` passes, your code will be automatically deployed. You can monitor
the progress of your deploy [here][jenkins].

[ocf]: https://www.ocf.berkeley.edu/
[ocfweb]: https://github.com/ocf/ocfweb/
[puppet]: https://github.com/ocf/puppet/
[pypi]: https://pypi.python.org/pypi/ocflib
[apt]: http://apt.ocf.berkeley.edu/
[jenkins]: https://jenkins.ocf.berkeley.edu/view/ocflib-deploy/
[debian-pkg]: http://apt.ocf.berkeley.edu/pool/main/p/python-ocflib/
[pre-commit]: http://pre-commit.com/
