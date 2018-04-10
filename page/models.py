#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.contrib.gis.db import models

##################################################
# WORLD BORDERS

class WorldBorder(models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.
    name = models.CharField(max_length=50)
    area = models.IntegerField()
    pop2005 = models.IntegerField('Population 2005')
    fips = models.CharField('FIPS Code', max_length=2)
    iso2 = models.CharField('2 Digit ISO', max_length=2)
    iso3 = models.CharField('3 Digit ISO', max_length=3)
    un = models.IntegerField('United Nations Code')
    region = models.IntegerField('Region Code')
    subregion = models.IntegerField('Sub-Region Code')
    lon = models.FloatField()
    lat = models.FloatField()

    # GeoDjango-specific: a geometry field (MultiPolygonField), and
    # overriding the default manager with a GeoManager instance.
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):  # __unicode__ on Python 2
        return self.name


# Auto-generated `LayerMapping` dictionary for WorldBorder model
worldborder_mapping = {
    'fips': 'FIPS',
    'iso2': 'ISO2',
    'iso3': 'ISO3',
    'un': 'UN',
    'name': 'NAME',
    'area': 'AREA',
    'pop2005': 'POP2005',
    'region': 'REGION',
    'subregion': 'SUBREGION',
    'lon': 'LON',
    'lat': 'LAT',
    'geom': 'MULTIPOLYGON',
}

##################################################
# ACTIVE FIRES

SOURCE_TYPE = (('MODIS-Aqua', 'MODIS-Aqua'),
               ('MODIS-Terra', 'MODIS-Terra'),
               ('VIIRS', 'VIIRS'))


class ActiveFire(models.Model):
    geom = models.PointField()  # Geodjango Point (longitude, latitude)
    date = models.DateTimeField()  # datetime: acq_date + acq_time (adjusted in Colombia zone -5h)
    source = models.CharField(choices=SOURCE_TYPE, max_length=20)  # from satellite
    brightness = models.FloatField()  # Brightness Temperature (Kelvin)
    confidence = models.PositiveIntegerField(null=True)  # Confidence (0–100%) or None (for VIIRS)
    frp = models.FloatField(null=True)  # Fire Radiative Power (MW) or None (for VIIRS)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['date', 'source']
