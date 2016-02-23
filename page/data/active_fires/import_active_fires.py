#
# #### How to run as script:
# ./manage.py shell < page/data/active_fires/import_active_fires.py
#
# #### How to run inline:
# python manage.py shell
# from page.data.active_fires import import_active_fires
# import_active_fires.modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'files', 'Global_MCD14DL_2014337.txt'))

import csv
import datetime
import os

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.gis.geos import Point

from page.models import ActiveFire
from page.models import WorldBorder


def save_csv(active_fire):
    ftp_path = os.path.join(settings.BASE_DIR, 'page', 'data', 'ftp_files')
    filename = 'Puntos_de_incendios_Colombia_{0}.csv'.format(active_fire.date.strftime("%Y-%m-%d"))
    if os.path.exists(os.path.join(ftp_path, filename)):
        csv_f = csv.writer(open(os.path.join(ftp_path, filename), 'a'), delimiter=',')
    else:
        csv_f = csv.writer(open(os.path.join(ftp_path, filename), 'w'), delimiter=',')
        csv_f.writerow(['DATE', 'LAT', 'LNG', 'SAT'])
    csv_f.writerow(
        [active_fire.date.strftime("%Y-%m-%d %H:%M"), active_fire.geom.y, active_fire.geom.x, active_fire.source])


def modis(active_fires_file):
    reader = csv.DictReader(open(active_fires_file, 'rt', encoding='utf8'), delimiter=",")
    colombia = WorldBorder.objects.get(name='Colombia')
    for line in reader:
        date = [int(i) for i in line['acq_date'].split('-')]
        time = [int(i) for i in line['acq_time'].split(':')]
        # time = list(str(line['acq_time']).strip())
        # time = [int(''.join(time[0:2])), int(''.join(time[2:4]))]
        lng = float(line['longitude'])
        lat = float(line['latitude'])
        active_fire_point = Point(lng, lat)
        active_fire_datetime = datetime.datetime(date[0], date[1], date[2], time[0], time[1]) + relativedelta(hours=-5)  # fix to Colombian zone
        source = 'MODIS-Aqua' if line['satellite'].strip() == 'A' else 'MODIS-Terra'
        brightness = float(line['brightness'])
        confidence = int(line['confidence'])
        frp = float(line['confidence'])

        if colombia.mpoly.contains(active_fire_point):
            print('Active fire inside Colombia?: yes')
            active_fire_count = ActiveFire.objects.filter(date=active_fire_datetime, source=source, geom=active_fire_point).count()
            if active_fire_count == 0:
                print('  Saving the point')
                active_fire = ActiveFire(geom=active_fire_point,
                                         date=active_fire_datetime,
                                         source=source,
                                         brightness=brightness,
                                         confidence=confidence,
                                         frp=frp,
                                         )
                save_csv(active_fire)
                active_fire.save()
            else:
                print('  Active fire exists!')
        else:
            pass
            # print('Active fire not inside Colombia',end='..')

# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'files', 'South_America_MCD14DL_2014342.txt'))
# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'firms1736314181687011_NRT.csv'))
# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'firms1736314181687011_MCD14ML.csv'))
