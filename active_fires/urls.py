from django.conf.urls import url
from django.contrib.gis import admin

from page import views, static_hotspot_files
from page.forms import Parameters
from djgeojson.views import GeoJSONLayerView
from page.models import ActiveFire

urlpatterns = [
    # Examples:
    # url(r'^$', 'active_fires.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', admin.site.urls),

    # master view and process
    url(r'^$', views.home, name='home'),
    # set new parameters from form by user
    url(r'^new-parameters/$', views.new_parameters, name='new_parameters'),
    # send data through ajax with geojson
    url(r'^data.geojson/$', views.ActiveFireMapLayer.as_view(model=ActiveFire, properties=('popup_text',)), name='data'),

    ###
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('es-CO',)}),

    ### for static ftp csv files of hostpot
    url(r'^ftp_files/(?P<path>.*)$', static_hotspot_files.serve, {'document_root': '/home/xavier/Projects/SMBYC/active_fires/static/ftp_files/', 'show_indexes': True}),
]
