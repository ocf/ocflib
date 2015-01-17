#!/bin/bash -e
# Release a new version of ocflib

# increment version number
version=$(grep '^VERSION = ' setup.py | cut -d' ' -f3)
version=$((version+1))
sed -i "s/^VERSION = .*/VERSION = $version/" setup.py

echo "Releasing new version $version..."

# clean up old stuff
python3 setup.py clean
[ -d dist ] && rm -r dist

# build and upload
python3 setup.py sdist
twine upload dist/*
