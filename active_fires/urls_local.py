#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
URLs used by `active_fires.settings_local`: the whole site plus a couple of
development-only helper pages. The production URLconf (`active_fires.urls`)
stays untouched.
"""

from django.contrib.staticfiles.views import serve as serve_static
from django.urls import path
from django.views.decorators.cache import never_cache

from active_fires.urls import urlpatterns as site_urlpatterns
from dev import views as dev_views

urlpatterns = site_urlpatterns + [
    path('_dev/responsive/', dev_views.responsive_check, name='dev-responsive-check'),
    path('_dev/responsive/report/', dev_views.responsive_report, name='dev-responsive-report'),

    # served here (runserver is started with --nostatic) only to add the
    # no-cache headers: its own static handler sends none, so browsers keep
    # serving an edited stylesheet from their cache
    path('static/<path:path>', never_cache(serve_static)),
]
