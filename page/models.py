#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django.contrib.gis.db import models


class WorldBorder(models.Model):
    name = models.CharField(max_length=50)
    area = models.IntegerField()
    pop2005 = models.IntegerField('Population 2005')
    fips = models.CharField('FIPS Code', max_length=2, null=True)
    iso2 = models.CharField('2 Digit ISO', max_length=2)
    iso3 = models.CharField('3 Digit ISO', max_length=3)
    un = models.IntegerField('United Nations Code')
    region = models.IntegerField('Region Code')
    subregion = models.IntegerField('Sub-Region Code')
    lon = models.FloatField()
    lat = models.FloatField()
    mpoly = models.MultiPolygonField()

    def __str__(self):
        return self.name


class ActiveFire(models.Model):

    class Source(models.TextChoices):
        MODIS_AQUA = 'MODIS-Aqua'
        MODIS_TERRA = 'MODIS-Terra'
        VIIRS = 'VIIRS'
        VIIRS_NOAA_20 = 'VIIRS-NOAA-20'
        VIIRS_NOAA_21 = 'VIIRS-NOAA-21'
        VIIRS_SUOMI_NPP = 'VIIRS-Suomi-NPP'

    class DayNight(models.TextChoices):
        DAY = 'D', 'Day'
        NIGHT = 'N', 'Night'

    geom = models.PointField()
    date = models.DateTimeField(db_index=True)
    source = models.CharField(choices=Source, max_length=20, db_index=True)
    brightness = models.FloatField()  # Kelvin — VIIRS: band 4, MODIS: Channel 21/22
    brightness_alt = models.FloatField(null=True, blank=True)  # Kelvin — VIIRS: band 5, MODIS: Channel 31
    confidence = models.CharField(null=True, blank=True, max_length=10)  # 0–100% (MODIS) or Baja/Nominal/Alta (VIIRS)
    frp = models.FloatField(null=True, blank=True)  # Fire Radiative Power (MW)
    day_night = models.CharField(choices=DayNight, max_length=1, null=True, blank=True)
    scan = models.FloatField(null=True, blank=True)  # actual pixel size (km)
    track = models.FloatField(null=True, blank=True)  # actual pixel size (km)

    def __str__(self):
        return f"ActiveFire {self.source} {self.date}"

    class Meta:
        ordering = ['date', 'source']
        indexes = [
            models.Index(fields=['date', 'source'], name='activefire_date_source_idx'),
        ]


class Region(models.Model):

    class Group(models.TextChoices):
        DEPARTAMENTOS = 'departamentos', 'Departamentos'
        REGIONES_NATURALES = 'regiones_naturales', 'Regiones Naturales'
        PARQUES_NACIONALES = 'parques_nacionales', 'Parques Nacionales'
        CORPORACIONES = 'corporaciones', 'Corporaciones'

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True, null=True, blank=True)
    group = models.CharField(choices=Group, max_length=30, null=True, blank=True)
    shape = models.MultiPolygonField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['group', 'name']


class BurnedArea(models.Model):

    class Source(models.TextChoices):
        MCD64A1 = 'MCD64A1'

    date = models.DateField(null=True, blank=True, db_index=True)
    slug = models.SlugField(max_length=80, unique=True, null=True, blank=True)
    source = models.CharField(choices=Source, max_length=20, null=True, blank=True)
    shape = models.MultiPolygonField()

    def __str__(self):
        return f"BurnedArea {self.slug or 'no-date'}"

    class Meta:
        ordering = ['-date']
