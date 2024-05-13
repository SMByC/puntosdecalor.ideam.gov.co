#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Django settings for Active_Fires project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Add the directory containing your local Python modules to python path
sys.path.insert(0, '/home/activefires/.local/lib/python3.9/site-packages')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm%tfjngc5i%%6m*mlt!oz_+l38ku+udds*^-j)bc=@2hd3zt!a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'leaflet',
    'djgeojson',
    'page',
)

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
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'SMBYC_active_fires',
        'USER': os.environ.get('db_username', 'postgres'),
        'PASSWORD': os.environ.get('db_password', ''),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'es-CO'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static_production')

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
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
    # 'DEFAULT_CENTER': (5, -72.0),
    # 'DEFAULT_ZOOM': 5,
    'SPATIAL_EXTENT': (-94.39453125, 16.130262012034756, -51.37207031249999, -6.970049417296218),
    'MIN_ZOOM': 5,
    'MAX_ZOOM': 17,
    'SCALE': 'metric',
    'MINIMAP': True,

    # http://leaflet-extras.github.io/leaflet-providers/preview/
    # apikey osm: http://www.thunderforest.com/docs/apikeys/
    # apikey mapbox: https://www.mapbox.com/studio/account/
    'TILES': [
        ('CartoDB', 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'),
        ('OpenStreetMap', 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'),
        ('Mapbox Outdoors', 'http://api.tiles.mapbox.com/v4/mapbox.outdoors/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoieGF2aWVyY2xsIiwiYSI6ImNqNmN6MGoxbDF3NmoyeHJ5OXoybWlidDkifQ.HbIa-_DLFoUCBVbHSCXWLQ', '&copy; OpenStreetMap Contributors'),
        ('Landscape', 'https://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=306c10ff32de428f99846994708aeaaa', '&copy; OpenStreetMap Contributors'),
        ('Esri World Image', 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', '&copy; Esri'),
        ('OpenCycleMap', 'https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=306c10ff32de428f99846994708aeaaa', '&copy; OpenStreetMap Contributors'),
        ('NatGeo', 'http://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}', '&copy; NatGeo'),
    ],

    #'OVERLAYS': [('Limites', 'http://openmapsurfer.uni-hd.de/tiles/adminb/x={x}&y={y}&z={z}', '&copy; IGN')],

}
