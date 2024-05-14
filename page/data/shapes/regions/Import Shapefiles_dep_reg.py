import os, sys, django
# setup django
project_dir = "/home/activefires/apps/Active_Fires"
if project_dir not in sys.path:
    sys.path.append(project_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "active_fires.settings")
django.setup()

# https://docs.djangoproject.com/en/1.11/ref/contrib/gis/layermapping/

## importar desde shape con un ID un solo poligono

#from django.contrib.gis.utils import LayerMapping
#from appweb.models import Region

#mapping = {'shape' : 'MULTIPOLYGON'}

#lm = LayerMapping(Region, '/home/xavier/nuevo/a.shp', mapping)

#lm.save(verbose=True)

#r = lm.model.objects.latest('id')
#r.name = "testname"
#r.save()

## DEPARTAMENTOS

from django.template.defaultfilters import slugify
from django.contrib.gis.utils import LayerMapping
from page.models import Region

mapping = {
    'name': 'Leyenda',
    'group': 'group',
    'shape': 'MULTIPOLYGON'}

lm = LayerMapping(Region, 'Departamentos.shp', mapping)

lm.save(verbose=True)

regions = lm.model.objects.all()

for region in regions:
    region.name = region.name.title()
    region.slug = slugify(region.name)
    region.save()

## REGIONES NATURALES

mapping = {
    'name': 'Regin',
    'group': 'group',
    'shape': 'MULTIPOLYGON'}

lm = LayerMapping(Region, 'Regiones_Naturales.shp', mapping)

lm.save(verbose=True)

regions = lm.model.objects.all()

for region in regions:
    region.name = region.name.title()
    region.slug = slugify(region.name)
    region.save()

