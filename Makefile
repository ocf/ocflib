# http://stackoverflow.com/a/23324703
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# run tests, linters, etc.
check: lint test

lint:
	flake8 ocflib

test:
	py.test tests

release: check
	./scripts/release.sh

# Install Python versions using pyenv, run tests with tox.
tox-pyenv: export PYENV_ROOT := $(ROOT_DIR)/.pyenv
tox-pyenv: export PATH := $(PYENV_ROOT)/shims:$(PYENV_ROOT)/bin:${PATH}
tox-pyenv: .pyenv/
	pyenv rehash
	tox

.pyenv/: export PYENV_ROOT := $(ROOT_DIR)/.pyenv
.pyenv/: export PATH := $(PYENV_ROOT)/shims:$(PYENV_ROOT)/bin:${PATH}
.pyenv/:
	git clone https://github.com/yyuu/pyenv.git .pyenv
	pyenv install 3.2.6
	pyenv install 3.4.3
	pyenv local 3.4.3 3.2.6
