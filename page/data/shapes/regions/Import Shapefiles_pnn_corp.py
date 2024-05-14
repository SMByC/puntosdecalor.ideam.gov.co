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


from django.template.defaultfilters import slugify
from django.contrib.gis.utils import LayerMapping
from page.models import Region


### Parques nacionales

mapping = {
    'name': 'nombre',
    'group': 'group',
    'shape': 'MULTIPOLYGON'}

lm = LayerMapping(Region, 'PNN.shp', mapping)

lm.save(verbose=True)

items = Region.objects.filter(group="parques_nacionales")

for item in items:
    item.slug = slugify(item.name)
    print(item.name)
    item.save()

### Corporaciones

mapping = {
    'name': 'Nombre',
    'group': 'group',
    'shape': 'MULTIPOLYGON'}

lm = LayerMapping(Region, 'Corporaciones.shp', mapping)

lm.save(verbose=True)

items = Region.objects.filter(group="corporaciones")

for item in items:
    item.slug = slugify(item.name)
    print(item.name)
    item.save()



