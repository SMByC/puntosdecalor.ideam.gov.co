from django.conf.urls import url
from django.contrib.gis import admin

from page import views, static_hotspot_files
from page.forms import Period
from djgeojson.views import GeoJSONLayerView
from page.models import HotspotFire

urlpatterns = [
    # Examples:
    # url(r'^$', 'Monitoreo_de_incendios.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', admin.site.urls),

    url(r'^$', views.init, name='init'),
    url(r'^load-period/$', views.home, name='load_period'),
    url(r'^(?P<from_year>[0-9]{4})-(?P<from_month>[0-9]{1,2})-(?P<from_day>[0-9]{1,2})/(?P<to_year>[0-9]{4})-(?P<to_month>[0-9]{1,2})-(?P<to_day>[0-9]{1,2})/$', views.home, name='home'),

    url(r'^data.geojson/(?P<from_year>[0-9]{4})-(?P<from_month>[0-9]{1,2})-(?P<from_day>[0-9]{1,2})/(?P<to_year>[0-9]{4})-(?P<to_month>[0-9]{1,2})-(?P<to_day>[0-9]{1,2})/$', views.HotspotMapLayer.as_view(model=HotspotFire, properties=('popup_text',)), name='data'),

    ###
    #url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('es-CO',)}),

    ### for static ftp csv files of hostpot
    url(r'^ftp_files/(?P<path>.*)$', static_hotspot_files.serve, {'document_root': '/home/xavier/Projects/SMBYC/Monitoreo_de_incendios/static/ftp_files/', 'show_indexes': True}),
]
