#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.conf.urls import url
from django.contrib.gis import admin

from page import views, static_hotspot_files
from page.models import ActiveFire

urlpatterns = [
    # Examples:
    # url(r'^$', 'active_fires.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', admin.site.urls),

    # master view and process
    url(r'^$', views.home, name='home'),
    # set new parameters from form by user
    url(r'^new-parameters/$', views.new_parameters, name='new_parameters'),
    # active fires points - send data through ajax with geojson
    url(r'^active_fires.geojson/$', views.ActiveFiresMapLayer.as_view(model=ActiveFire, properties=('id',)), name='active-fires'),
    # get popup information
    url(r'^get_popup.geojson/$', views.get_popup, name='get-popup'),

    ### for static ftp csv files of hostpot
    url(r'^archivos-ftp/(?P<path>.*)$', static_hotspot_files.serve, {'document_root': '/home/activefires/apps/Active_Fires/page/data/ftp_files', 'show_indexes': True}),
]
