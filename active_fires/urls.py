#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.conf import settings
from django.urls import path
from django.contrib.gis import admin

from page import views, static_hotspot_files

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    # GeoJSON API endpoints
    path('region.geojson/', views.RegionMapLayer.as_view(), name='region'),
    path('burned_area.geojson/', views.BurnedAreaMapLayer.as_view(), name='burned-area'),
    path('active_fires.geojson/', views.ActiveFiresMapLayer.as_view(), name='active-fires'),
    path('get_popup.geojson/', views.get_popup, name='get-popup'),

    # CSV download
    path('download-result/', views.download_result, name='download-result'),

    # static CSV files of hotspot data
    path('archivos-ftp/', static_hotspot_files.ftp_2_csv_redirect, {'path': ''}, name='ftp-csv-redirect-root'),
    path('archivos-ftp/<path:path>', static_hotspot_files.ftp_2_csv_redirect, name='ftp-csv-redirect'),
    path('archivos-csv/', static_hotspot_files.serve, {
        'path': '',
        'document_root': str(settings.BASE_DIR / 'page' / 'data' / 'ftp_files'),
        'show_indexes': True,
    }, name='csv-index'),
    path('archivos-csv/<path:path>', static_hotspot_files.serve, {
        'document_root': str(settings.BASE_DIR / 'page' / 'data' / 'ftp_files'),
        'show_indexes': True,
    }),
]
