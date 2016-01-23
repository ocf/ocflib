# http://stackoverflow.com/a/23324703
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# first set COVERALLS_REPO_TOKEN=<repo token> environment variable
coveralls: test
	.tox/py34/bin/coveralls

test:
	tox

release-pypi: clean autoversion
	python3 setup.py sdist
	twine upload dist/*

builddeb: autoversion
	dpkg-buildpackage -us -uc -b

clean: autoversion
	python3 setup.py clean
	rm -rf dist deb_dist

# PEP440 sets terrible restrictions on public version schemes which prohibit:
#   - appending a SHA
#   - leading zeros before version components (e.g. "09" for September becomes "9")
# Unfortunately, PyPI enforces these restrictions.
autoversion:
	date +%Y.%-m.%-d.%-H.%-M > .version
	rm -f debian/changelog
	DEBFULLNAME="Open Computing Facility" DEBEMAIL="help@ocf.berkeley.edu" VISUAL=true \
		dch -v `cat .version` -D stable --no-force-save-on-release \
		--create --force-distribution --package "python-ocflib" "Package for Debian."
