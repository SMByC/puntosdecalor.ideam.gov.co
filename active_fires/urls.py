#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.conf import settings
from django.urls import path
from django.contrib.gis import admin
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from page import views, static_hotspot_files, sitemaps
from page.static_hotspot_files import (
    HOTSPOT_INDEX_TITLE, HOTSPOT_INDEX_INFO,
    BURNED_AREA_INDEX_TITLE, BURNED_AREA_INDEX_INFO,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # discovery files for search engines and AI agents (no trailing slash:
    # crawlers request these paths verbatim)
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain'), name='robots-txt'),
    path('sitemap.xml', sitemap, {'sitemaps': {'static': sitemaps.StaticSitemap}},
         name='sitemap'),
    path('llms.txt', TemplateView.as_view(
        template_name='llms.txt', content_type='text/markdown'), name='llms-txt'),

    path('', views.home, name='home'),

    # GeoJSON API endpoints
    path('region.geojson/', views.RegionMapLayer.as_view(), name='region'),
    path('burned_area.geojson/', views.BurnedAreaMapLayer.as_view(), name='burned-area'),
    path('active_fires.json/', views.active_fires_data, name='active-fires-data'),
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
        'index_title': HOTSPOT_INDEX_TITLE,
        'index_info': HOTSPOT_INDEX_INFO,
    }, name='csv-index'),
    path('archivos-csv/<path:path>', static_hotspot_files.serve, {
        'document_root': str(settings.BASE_DIR / 'page' / 'data' / 'ftp_files'),
        'show_indexes': True,
        'index_title': HOTSPOT_INDEX_TITLE,
        'index_info': HOTSPOT_INDEX_INFO,
    }),

    # static ZIP files of burned area data
    path('archivos-area-quemada/', static_hotspot_files.serve, {
        'path': '',
        'document_root': str(settings.BASE_DIR / 'page' / 'data' / 'ftp_ba_files'),
        'show_indexes': True,
        'index_title': BURNED_AREA_INDEX_TITLE,
        'index_info': BURNED_AREA_INDEX_INFO,
    }, name='ba-zip-index'),
    path('archivos-area-quemada/<path:path>', static_hotspot_files.serve, {
        'document_root': str(settings.BASE_DIR / 'page' / 'data' / 'ftp_ba_files'),
        'show_indexes': True,
        'index_title': BURNED_AREA_INDEX_TITLE,
        'index_info': BURNED_AREA_INDEX_INFO,
    }),
]
