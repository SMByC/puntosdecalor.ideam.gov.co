"""
Django settings for Active_Fires project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm%tfjngc5i%%6m*mlt!oz_+l38ku+udds*^-j)bc=@2hd3zt!a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

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

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
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
        'USER': 'postgres',

    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'es-CO'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

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
    # 'SPATIAL_EXTENT': (-79.2, -4,4, -66.7, 13.0),
    # 'SPATIAL_EXTENT': (-78, -3, -65, 12),

    'DEFAULT_CENTER': (5, -72.0),
    'DEFAULT_ZOOM': 5,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 15,

    # http://leaflet-extras.github.io/leaflet-providers/preview/
    'TILES': [
        ('Landscape', 'http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png', '&copy; OpenStreetMap Contributors'),
        ('Esri DeLorme', 'http://server.arcgisonline.com/ArcGIS/rest/services/Specialty/DeLorme_World_Base_Map/MapServer/tile/{z}/{y}/{x}', '&copy; Esri'),
        ('Esri World Image', 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', '&copy; Esri'),
        # ('Here', 'http://{s}.aerial.maps.cit.api.here.com/maptile/2.1/maptile/newest/hybrid.day/{z}/{x}/{y}/256/png8?app_id=1&app_code=1', '&copy; HERE'),
        ('Roads', 'http://openmapsurfer.uni-hd.de/tiles/roads/x={x}&y={y}&z={z}', '&copy; OpenStreetMap Contributors'),
        ('OSM DE', 'http://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', '&copy; OpenStreetMap Contributors'),
        ('OSM Cycle', 'http://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png', '&copy; OpenStreetMap Contributors'),
        ('NatGeo', 'http://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}', '&copy; NatGeo'),
    ],

    'OVERLAYS': [('Limites', 'http://openmapsurfer.uni-hd.de/tiles/adminb/x={x}&y={y}&z={z}', '&copy; IGN')],

    'MINIMAP': True,
    'SCALE': 'metric',
    'RESET_VIEW': False,

}
