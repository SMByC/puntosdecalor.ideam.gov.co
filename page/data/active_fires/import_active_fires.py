#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

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


def save_in_csv_table(active_fire):
    ftp_path = os.path.join(settings.BASE_DIR, 'page', 'data', 'ftp_files')
    filename = 'Puntos_de_calor_Colombia_{0}.csv'.format(active_fire.date.strftime("%Y-%m-%d"))
    if os.path.exists(os.path.join(ftp_path, filename)):
        csv_f = csv.writer(open(os.path.join(ftp_path, filename), 'a'), delimiter=';')
    else:
        csv_f = csv.writer(open(os.path.join(ftp_path, filename), 'w'), delimiter=';')
        csv_f.writerow(['Fecha (UTC-5)', 'Lat', 'Lon', 'Fuente', 'Temperatura (C)', 'Temperatura Alt* (C)',
                        'Radiación térmica (MW)', 'Confianza', 'Captura (Dia-Noche)',
                        'Scan - real pixel size (km)', 'Track - real pixel size (km)'])
    csv_f.writerow([
        active_fire.date.strftime("%Y-%m-%d %H:%M"), str(active_fire.geom.y).replace(".", ","),
        str(active_fire.geom.x).replace(".", ","), active_fire.source,
        '' if active_fire.brightness is None else str(round(active_fire.brightness - 273.15, 1)).replace(".", ","),
        '' if active_fire.brightness_alt is None else str(round(active_fire.brightness_alt - 273.15, 1)).replace(".", ","),
        '' if active_fire.frp is None else str(active_fire.frp).replace(".", ","),
        '' if active_fire.confidence is None else active_fire.confidence,
        '' if active_fire.day_night is None else active_fire.day_night,
        '' if active_fire.scan is None else str(active_fire.scan).replace(".", ","),
        '' if active_fire.track is None else str(active_fire.track).replace(".", ","),
        ])


def from_source(source=None, csv_input_file=None):
    reader = csv.DictReader(open(csv_input_file, 'rt', encoding='utf8'), delimiter=",")
    colombia = WorldBorder.objects.get(name='Colombia')
    for line in reader:
        date = [int(i) for i in line['acq_date'].split('-')]

        if ":" in line['acq_time']:
            time = [int(i) for i in line['acq_time'].split(':')]
        else:
            # split hhmm into hh and mm, e.g. 1230 -> [12, 30], 545 -> [5, 45]
            time = [int(line['acq_time'][-4:-2]), int(line['acq_time'][-2:])]

        lng = float(line['longitude'])
        lat = float(line['latitude'])
        active_fire_point = Point(lng, lat)
        active_fire_datetime = datetime.datetime(date[0], date[1], date[2], time[0], time[1]) + relativedelta(hours=-5)  # fix to Colombian zone

        if source is None:
            if line['satellite'].strip() in ('A', 'T', 'Aqua', 'Terra'):
                source = 'modis'
            elif line['satellite'] == 'N':
                source = 'viirs-suomi-npp'
            elif line['satellite'] == 'N20':
                source = 'viirs-noaa-20'
            elif line['satellite'] == 'N21':
                source = 'viirs-noaa-21'

        if source == 'modis':
            satellite = 'MODIS-Aqua' if line['satellite'].strip() in ('A', 'Aqua') else 'MODIS-Terra'
            # Brightness Temperature
            brightness = float(line['brightness'])
            brightness_alt = float(line['bright_t31'])
            # Confidence
            confidence = f"{line['confidence']} %"
        if source == 'viirs':  # old, not currently used
            satellite = 'VIIRS'
            # Brightness Temperature
            brightness = float(line['bright_ti4'])
            # Confidence
            confidence = None
        if source in ('viirs-noaa-20', 'viirs-noaa-21', 'viirs-suomi-npp'):
            if source == 'viirs-noaa-20':
                satellite = 'VIIRS-NOAA-20'
            elif source == 'viirs-noaa-21':
                satellite = 'VIIRS-NOAA-21'
            elif source == 'viirs-suomi-npp':
                satellite = 'VIIRS-Suomi-NPP'
            # Brightness Temperature
            brightness = float(line['bright_ti4'])
            brightness_alt = float(line['bright_ti5'])
            # Confidence
            if line['confidence'] in ('l', 'n', 'h'):
                confidence = {'l': 'Baja', 'n': 'Nominal', 'h': 'Alta'}.get(line['confidence'])
            else:
                confidence = {'low': 'Baja', 'nominal': 'Nominal', 'high': 'Alta'}.get(line['confidence'])

        # Fire Radiative Power
        frp = round(float(line['frp']), 1)
        if int(frp) == 0:
            frp = None
        # Others
        day_night = line['daynight']
        scan = float(line['scan'])
        track = float(line['track'])

        if colombia.mpoly.contains(active_fire_point):
            print('Active fire inside Colombia?: yes')
            active_fire_count = ActiveFire.objects.filter(date=active_fire_datetime, source=satellite, geom=active_fire_point).count()
            if active_fire_count == 0:
                print('  Saving the point')
                active_fire = ActiveFire(geom=active_fire_point,
                                         date=active_fire_datetime,
                                         source=satellite,
                                         brightness=brightness,
                                         brightness_alt=brightness_alt,
                                         confidence=confidence,
                                         frp=frp,
                                         day_night=day_night,
                                         scan=scan,
                                         track=track,
                                         )
                save_in_csv_table(active_fire)
                active_fire.save()
            else:
                print('  Active fire exists!')
        else:
            pass
            # print('Active fire not inside Colombia',end='..')

# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'files', 'South_America_MCD14DL_2014342.txt'))
# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'firms1736314181687011_NRT.csv'))
# modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'active_fires', 'modis', 'firms1736314181687011_MCD14ML.csv'))
