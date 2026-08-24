#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Django settings for Active_Fires project.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

import os

from django.core.exceptions import ImproperlyConfigured

# SECURITY WARNING: keep the secret key used in production secret!
# No fallback on purpose: a default here is public in this repo, and it would
# sign real sessions, CSRF tokens and signed cookies from the moment the key
# failed to reach the process, with nothing in the logs to say so.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is not set. In production it comes from "
        "/home/activefires/apps/Active_Fires/.env; for local development run "
        "with DJANGO_SETTINGS_MODULE=active_fires.settings_local."
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# the production domains served by nginx (`active_fires_nginx.conf`); anything
# else answers with a 400 before touching the views. The leading dot matches
# the apex and any subdomain (including www) to stay aligned with nginx's
# wildcard server_name. Local development overrides this in
# `active_fires.settings_local`. If prod health-checks ping by IP, ensure
# they send Host: puntosdecalor.ideam.gov.co.
ALLOWED_HOSTS = ['.puntosdecalor.ideam.gov.co']

# Preserve existing primary key type (AutoField) for models created
# before Django 3.2. Without this, Django 6.0 defaults to BigAutoField
# which would require migrating all existing integer PKs to bigint.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.gis',
    'leaflet',
    'djgeojson',
    'page.apps.PageConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'active_fires.urls'

WSGI_APPLICATION = 'active_fires.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'SMBYC_active_fires',
        'USER': os.environ.get('db_username', 'postgres'),
        'PASSWORD': os.environ.get('db_password', ''),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-CO'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_ROOT = BASE_DIR / 'static_production'

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Every static file is served under a name carrying a hash of its content
# (active_fires.2e3e70a06658.css), so a deployed change reaches every visitor
# on their next page load instead of waiting for whatever the browser decided
# to cache, and unchanged files keep being served from the cache.
#
# This needs `manage.py collectstatic` on every deploy: the names come from the
# manifest it writes, and a file missing from it raises instead of being served
# under its plain name.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Leaflet configuration
LEAFLET_CONFIG = {
    # map boundaries limits
    'SPATIAL_EXTENT': (-94.39453125, 16.130262012034756, -51.37207031249999, -6.970049417296218),
    'MIN_ZOOM': 5,
    'MAX_ZOOM': 17,
    'SCALE': 'metric',
    'MINIMAP': True,

    # http://leaflet-extras.github.io/leaflet-providers/preview/
    'TILES': [
        ('CartoDB', 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'),
        ('OpenStreetMap', 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'),
        ('Mapbox Outdoors', f'http://api.tiles.mapbox.com/v4/mapbox.outdoors/{{z}}/{{x}}/{{y}}.png?access_token={os.environ.get("MAPBOX_ACCESS_TOKEN", "")}', '&copy; OpenStreetMap Contributors'),
        ('Landscape', f'https://{{s}}.tile.thunderforest.com/landscape/{{z}}/{{x}}/{{y}}.png?apikey={os.environ.get("THUNDERFOREST_API_KEY", "")}', '&copy; OpenStreetMap Contributors'),
        ('Esri World Image', 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', '&copy; Esri'),
        ('OpenCycleMap', f'https://{{s}}.tile.thunderforest.com/cycle/{{z}}/{{x}}/{{y}}.png?apikey={os.environ.get("THUNDERFOREST_API_KEY", "")}', '&copy; OpenStreetMap Contributors'),
        ('NatGeo', 'http://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}', '&copy; NatGeo'),
    ],
}
