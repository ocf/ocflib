# run tests, linters, etc.
check: lint

lint:
	flake8 ocflib

release: check
	./scripts/release.sh
