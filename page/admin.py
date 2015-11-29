from django.contrib.gis import admin
from page.models import WorldBorder, HotspotFire

admin.site.register(WorldBorder, admin.GeoModelAdmin)
admin.site.register(HotspotFire, admin.GeoModelAdmin)