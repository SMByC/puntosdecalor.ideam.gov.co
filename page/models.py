from django.contrib.gis.db import models

# Create your models here.

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
    objects = models.GeoManager()

    # Returns the string representation of the model.
    def __str__(self):              # __unicode__ on Python 2
        return self.name

# Auto-generated `LayerMapping` dictionary for WorldBorder model
worldborder_mapping = {
    'fips' : 'FIPS',
    'iso2' : 'ISO2',
    'iso3' : 'ISO3',
    'un' : 'UN',
    'name' : 'NAME',
    'area' : 'AREA',
    'pop2005' : 'POP2005',
    'region' : 'REGION',
    'subregion' : 'SUBREGION',
    'lon' : 'LON',
    'lat' : 'LAT',
    'geom' : 'MULTIPOLYGON',
}

################

SOURCE_TYPE = (('MODIS-Aqua', 'MODIS-Aqua'),
               ('MODIS-Terra', 'MODIS-Terra'),
               ('VIIRS','VIIRS'))

class HotspotFire(models.Model):

    geom = models.PointField()
    date = models.DateTimeField()
    source = models.CharField(choices = SOURCE_TYPE, max_length=20)
    brightness = models.FloatField()
    popup_text = models.TextField(null = True, blank = True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['date', 'source']

    def get_popup_text(self):
        return '<p>Fecha: {datetime}<br />Brillo: {brightness}<br />Satelite: {source}</p>'.format(
            datetime=self.date.strftime("%Y-%m-%d %H:%M"), brightness=self.brightness,source=self.source
        )

    def save(self, *args, **kwargs):
        # set the popup_text of hotspot
        if not self.popup_text:
           self.popup_text = self.get_popup_text()
        super(HotspotFire, self).save(*args, **kwargs)