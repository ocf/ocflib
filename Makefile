# run tests, linters, etc.
check: lint test

lint:
	flake8 ocflib

test:
	py.test tests

release: check
	./scripts/release.sh
