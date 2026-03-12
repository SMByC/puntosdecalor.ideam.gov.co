#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.contrib.gis import admin
from page.models import WorldBorder, ActiveFire

admin.site.register(WorldBorder, admin.GISModelAdmin)
admin.site.register(ActiveFire, admin.GISModelAdmin)
