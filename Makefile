# first set COVERALLS_REPO_TOKEN=<repo token> environment variable
.PHONY: coveralls
coveralls: test
	.tox/py34/bin/coveralls

venv: setup.py requirements-dev.txt
	bin/venv-update -ppython3 venv -- -r requirements-dev.txt -e .

.PHONY: test
test:
	tox

.PHONY: release-pypi
release-pypi: clean autoversion
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: builddeb
builddeb: autoversion
	dpkg-buildpackage -us -uc

.PHONY: clean
clean: autoversion
	python3 setup.py clean
	rm -rf dist deb_dist

# PEP440 sets terrible restrictions on public version schemes which prohibit:
#   - appending a SHA
#   - leading zeros before version components (e.g. "09" for September becomes "9")
# Unfortunately, PyPI enforces these restrictions.
.PHONY: autoversion
autoversion:
	date +%Y.%-m.%-d.%-H.%-M > .version
	rm -f debian/changelog
	DEBFULLNAME="Open Computing Facility" DEBEMAIL="help@ocf.berkeley.edu" VISUAL=true \
		dch -v `cat .version` -D stable --no-force-save-on-release \
		--create --force-distribution --package "python-ocflib" "Package for Debian."
