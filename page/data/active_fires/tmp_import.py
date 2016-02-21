import os
from page.data.active_fires.import_hotspots import modis
from django.conf import settings
modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'files', 'South_America_MCD14DL_2014352.txt'))
