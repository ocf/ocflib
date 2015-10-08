# http://stackoverflow.com/a/23324703
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# run tests, linters, etc.
check: lint test

lint:
	pre-commit run --all-files

test: autoversion
	coverage erase
	coverage run --source=ocflib,tests -m pytest -v tests
	coverage report --show-missing

# first set COVERALLS_REPO_TOKEN=<repo token> environment variable
coveralls: tox
	tox -e coveralls

tox: autoversion
	tox

release-pypi: clean autoversion
	python3 setup.py sdist
	twine upload dist/*

builddeb: autoversion
	dpkg-buildpackage -us -uc -b

clean: autoversion
	python3 setup.py clean
	rm -rf dist deb_dist

# PEP440 sets restrictions on public version schemes which prohibit appending a
# SHA; unfortunately, PyPI enforces this restriction
autoversion:
	date +%Y.%m.%d.%H.%M > .version
	rm -f debian/changelog
	DEBFULLNAME="Open Computing Facility" DEBEMAIL="help@ocf.berkeley.edu" VISUAL=true \
		dch -v `cat .version` -D stable --no-force-save-on-release \
		--create --force-distribution --package "python-ocflib" "Package for Debian."

.pyenv/: export PYENV_ROOT := $(ROOT_DIR)/.pyenv
.pyenv/: export PATH := $(PYENV_ROOT)/shims:$(PYENV_ROOT)/bin:${PATH}
.pyenv/:
	git clone https://github.com/yyuu/pyenv.git .pyenv
	pyenv install 3.2.6
	pyenv install 3.4.3
	pyenv local 3.4.3 3.2.6
