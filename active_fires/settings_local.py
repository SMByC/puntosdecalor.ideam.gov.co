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

from .settings import *  # noqa: F401,F403
from .settings import BASE_DIR

DEBUG = True

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

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

# a fixed key is fine locally, it is never used to protect anything
SECRET_KEY = 'local-development-only-not-a-secret'
