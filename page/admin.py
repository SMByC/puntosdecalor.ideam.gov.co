#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.contrib.gis import admin
from page.models import WorldBorder, ActiveFire

admin.site.register(WorldBorder, admin.GeoModelAdmin)
admin.site.register(ActiveFire, admin.GeoModelAdmin)