import csv
import datetime
import os

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.gis.geos import Point

from page.models import HotspotFire
from page.models import WorldBorder


# run
# ./manage.py shell < page/data/hotspots_fire/import_hotspots.py

# run 2
# python manage.py shell
# from page.data.hotspots_fire import import_hotspots
# import_hotspots.modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'hotspots_fire', 'modis', 'files', 'Global_MCD14DL_2014337.txt'))

def save_csv(hotspot_fire):
    ftp_path = os.path.join(settings.BASE_DIR, 'page', 'data', 'ftp_files')
    filename = 'Puntos_de_incendios_Colombia_{0}.csv'.format(hotspot_fire.date.strftime("%Y-%m-%d"))
    if os.path.exists(os.path.join(ftp_path, filename)):
        csv_f = csv.writer(open(os.path.join(ftp_path, filename), 'a'), delimiter=',')
    else:
        csv_f = csv.writer(open(os.path.join(ftp_path, filename), 'w'), delimiter=',')
        csv_f.writerow(['DATE', 'LAT', 'LNG', 'SAT'])
    csv_f.writerow(
        [hotspot_fire.date.strftime("%Y-%m-%d %H:%M"), hotspot_fire.geom.y, hotspot_fire.geom.x, hotspot_fire.source])


def modis(hotspots_file):
    reader = csv.DictReader(open(hotspots_file, 'rt', encoding='utf8'), delimiter=",")
    colombia = WorldBorder.objects.get(name='Colombia')
    for line in reader:
        date = [int(i) for i in line['acq_date'].split('-')]
        time = [int(i) for i in line['acq_time'].split(':')]
        # time = list(str(line['acq_time']).strip())
        # time = [int(''.join(time[0:2])), int(''.join(time[2:4]))]
        lng = float(line['longitude'])
        lat = float(line['latitude'])
        hotspot_datetime = datetime.datetime(date[0], date[1], date[2], time[0], time[1]) + relativedelta(hours=-5)  # fix to Colombian zone
        source = 'MODIS-Aqua' if line['satellite'].strip() == 'A' else 'MODIS-Terra'
        brightness = line['brightness']
        # print(hotspot_datetime)
        # print(source)
        # print(brightness)
        # print(lat)
        # print(lng)
        pnt_hotspot = Point(lng, lat)
        if colombia.mpoly.contains(pnt_hotspot):
            print('Hotspot inside Colombia: yes')
            point = Point(lng, lat)
            hotspot_count = HotspotFire.objects.filter(date=hotspot_datetime, source=source, geom=point).count()
            if hotspot_count == 0:
                print('  Saving the point')
                hotspot_fire = HotspotFire(date=hotspot_datetime, source=source, brightness=brightness,
                                           geom=Point(lng, lat))
                save_csv(hotspot_fire)
                hotspot_fire.save()
            else:
                print('  Point exists!')
        else:
            pass
            # print('Hotspot not inside Colombia',end='..')

# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'hotspots_fire', 'modis', 'files', 'South_America_MCD14DL_2014342.txt'))
# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'hotspots_fire', 'modis', 'firms1736314181687011_NRT.csv'))
# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'hotspots_fire', 'modis', 'firms1736314181687011_MCD14ML.csv'))
