# SPDX-License-Identifier: GPL-3.0

PKGNAME = amethyst-ttkvlib
PKG_VERSION = $(shell python3 -c 'import re; print(re.search("__version__ = \"([\d.]+)\"", open("amethyst/ttkvlib/__init__.py").read()).group(1))')
PY_PATHS = amethyst/ttkvlib tests

.PHONY: all sdist dist debbuild clean test


check:
	@find amethyst tests setup.py -type f -not -empty -exec perl -nE '($$hit = 1), exit if /SPDX\-License\-Identifier/; END { $$hit or say "$$ARGV: MISSING SPDX-License-Identifier" }' {} \;
	python3 -m flake8 --config=extra/flake8.ini ${PY_PATHS}
	@echo OK

clean:
	rm -rf build dist debbuild amethyst_ttkvlib.egg-info
	rm -f MANIFEST
	pyclean .

debbuild: test sdist
	@head -n1 debian/changelog | grep "(${PKG_VERSION}-1)" debian/changelog || (/bin/echo -e "\e[1m\e[91m** debian/changelog requires update **\e[0m" && false)
	rm -rf debbuild
	mkdir -p debbuild
	mv -f dist/${PKGNAME}-${PKG_VERSION}.tar.gz debbuild/${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cd debbuild && tar -xzf ${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cp -r debian debbuild/${PKGNAME}-${PKG_VERSION}/
	cd debbuild/${PKGNAME}-${PKG_VERSION} && dpkg-buildpackage -rfakeroot -uc -us

dist: test debbuild
	@mkdir -p dist/${PKG_VERSION}
	mv -f debbuild/${PKGNAME}_* debbuild/*.deb dist/${PKG_VERSION}/
	rm -rf debbuild

sdist: test
	python3 setup.py sdist

test:
	python3 -m pytest --cov=amethyst/ --cov-branch --cov-report=html:_coverage tests

zip: test
	python3 setup.py sdist --format=zip
