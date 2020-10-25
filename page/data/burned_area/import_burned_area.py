#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2020
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

import os, sys, django
from django.contrib.gis.utils import LayerMapping
# setup django
project_dir = "/home/activefires/apps/Active_Fires"
if project_dir not in sys.path:
    sys.path.append(project_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "active_fires.settings")
django.setup()

from page.models import BurnedArea


def from_source(source, burned_area_file, ba_date):

    # check if exists
    if BurnedArea.objects.filter(slug=ba_date.strftime("%Y-%m")).first():
        print('Burned area already exists!')
        return

    mapping = {'shape': 'MULTIPOLYGON'}
    lm = LayerMapping(BurnedArea, burned_area_file, mapping)
    lm.save(verbose=True)

    burned_area = BurnedArea.objects.latest('id')
    burned_area.slug = ba_date.strftime("%Y-%m")
    burned_area.source = source
    burned_area.save()

