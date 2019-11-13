venv: setup.py requirements-dev.txt
	vendor/venv-update \
		venv= $@ -ppython3 \
		install= -r requirements-dev.txt -e .

.PHONY: install-hooks
install-hooks: venv
	venv/bin/pre-commit install

# set COVERALLS_REPO_TOKEN=<repo token> environment variable to report coverage
# after running tests
.PHONY: test
test:
	tox
ifneq ($(strip $(COVERALLS_REPO_TOKEN)),)
	.tox/py35/bin/coveralls
endif

.PHONY: release-pypi
release-pypi: clean autoversion
	python3 setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: builddeb
builddeb: autoversion
	dpkg-buildpackage -us -uc

.PHONY: package
package: package_stretch

.PHONY: package_%
package_%:
	docker run -e "DIST_UID=$(shell id -u)" -e "DIST_GID=$(shell id -g)" -v $(CURDIR):/mnt:rw "docker.ocf.berkeley.edu/theocf/debian:$*" /mnt/build-in-docker "$*"

.PHONY: clean
clean:
	python3 setup.py clean
	rm -rf dist deb_dist dist_*

# PEP440 sets terrible restrictions on public version schemes which prohibit:
#   - appending a SHA
#   - leading zeros before version components (e.g. "09" for September becomes "9")
# Unfortunately, PyPI enforces these restrictions.
.PHONY: autoversion
autoversion:
	date +%Y.%-m.%-d.%-H.%-M > .version
	rm -f debian/changelog
	DEBFULLNAME="Open Computing Facility" DEBEMAIL="help@ocf.berkeley.edu" \
		dch -v `cat .version` -D stable --no-force-save-on-release \
		--create --force-distribution --package "python-ocflib" "Package for Debian."
	dch --local "~deb$(shell lsb_release -rs | cut -d . -f 1)u" \
                "Package for $(shell lsb_release -cs)."
