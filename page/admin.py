from django.contrib.gis import admin
from page.models import WorldBorder, ActiveFire

admin.site.register(WorldBorder, admin.GeoModelAdmin)
admin.site.register(ActiveFire, admin.GeoModelAdmin)