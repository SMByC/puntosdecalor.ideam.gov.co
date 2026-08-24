#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Local development settings: the whole site on SQLite/SpatiaLite.

This keeps production settings untouched and lets anyone run the page without
a PostGIS server:

    make dev                    # environment + database + demo data + server

or by hand:

    DJANGO_SETTINGS_MODULE=active_fires.settings_local python manage.py runserver

Requires the SpatiaLite extension of SQLite (package `libspatialite`, which
provides `mod_spatialite`). Override its path if it is not found automatically:

    SPATIALITE_LIBRARY_PATH=/opt/homebrew/lib/mod_spatialite.dylib make run

NEVER use this module in production.
"""

import os

# settings.py refuses to start without DJANGO_SECRET_KEY. Development has no
# .env, so seed the value the star import below reads, then take it back out:
# left in the environment it is inherited by every subprocess (dev/
# responsive_check.py passes dict(os.environ, ...)), and one of those running
# under active_fires.settings would silently start on this key.
_DEV_SECRET_KEY = 'local-development-only-not-a-secret'
_seeded_secret_key = 'DJANGO_SECRET_KEY' not in os.environ
if _seeded_secret_key:
    os.environ['DJANGO_SECRET_KEY'] = _DEV_SECRET_KEY

from .settings import *  # noqa: E402,F401,F403
from .settings import BASE_DIR  # noqa: E402

if _seeded_secret_key:
    del os.environ['DJANGO_SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

# The hashed names of the production storage come from the manifest that
# collectstatic writes, which does not exist here: development serves the files
# straight out of STATICFILES_DIRS, under their own names.
STORAGES = {
    **STORAGES,  # noqa: F405
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# SQLite + SpatiaLite instead of PostGIS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.environ.get('LOCAL_DB_PATH', str(BASE_DIR / 'local_dev.sqlite3')),
    }
}

# Name (or full path) of the SpatiaLite loadable extension, only when given:
# django probes 'mod_spatialite.so', 'mod_spatialite' and find_library()
# on its own, but as soon as this setting exists the first failure is fatal
# instead of falling through to the other names.
_spatialite_library = os.environ.get('SPATIALITE_LIBRARY_PATH')
if _spatialite_library:
    SPATIALITE_LIBRARY_PATH = _spatialite_library

# the site URLs plus the development-only helper pages (responsive check)
ROOT_URLCONF = 'active_fires.urls_local'

# the responsive check loads the page in an iframe of /_dev/responsive/;
# django defaults to DENY, which blocks framing even from the same origin
X_FRAME_OPTIONS = 'SAMEORIGIN'

# a fixed key is fine locally, it protects nothing. This also wins over a real
# DJANGO_SECRET_KEY that happens to be exported in the developer's environment
SECRET_KEY = _DEV_SECRET_KEY
