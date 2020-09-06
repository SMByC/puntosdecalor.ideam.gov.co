#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.urls import path, re_path
from django.contrib.gis import admin

from page import views, static_hotspot_files
from page.models import ActiveFire, Region

urlpatterns = [
    path('admin/', admin.site.urls),

    # master view and process
    path('', views.home, name='home'),
    # get region
    path('region.geojson/', views.RegionMapLayer.as_view(model=Region, geometry_field='shape', properties=('name')), name='region'),
    # active fires points - send data through ajax with geojson
    path('active_fires.geojson/', views.ActiveFiresMapLayer.as_view(model=ActiveFire, properties=('id',)), name='active-fires'),
    # get popup information
    path('get_popup.geojson/', views.get_popup, name='get-popup'),
    # download active fires points
    path('download-result/', views.download_result, name='download-result'),

    ### for static ftp csv files of hostpot
    re_path(r'^archivos-ftp/(?P<path>.*)$', static_hotspot_files.serve, {'document_root': '/home/activefires/apps/Active_Fires/page/data/ftp_files', 'show_indexes': True}),
]
