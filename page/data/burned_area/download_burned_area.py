#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2020
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

# use:
#
# cd /home/activefires/apps/Active_Fires/page/data/burned_area
#  python3.8 download_burned_area.py -s mcd64a1 -d 2020-1
#
# DATA SOURCES:
# https://modis-fire.umd.edu/index.html

import glob
import shutil
import sys, os
from time import sleep
from datetime import date
from dateutil.relativedelta import relativedelta

# setup django
import django
project_dir = "/home/activefires/apps/Active_Fires"
if project_dir not in sys.path:
    sys.path.append(project_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "active_fires.settings")
django.setup()

from page.models import BurnedArea

os.chdir(os.path.dirname(os.path.realpath(__file__)))

######
from configparser import ConfigParser
cfg = ConfigParser()
cfg.read(os.path.join('donwload_config.ini'))

######
import argparse

parser = argparse.ArgumentParser(description='Import burned area from MCD64A1 to database')
parser.add_argument('-d', dest='date', action='store', required=True,
                    help='Day to run the process format: "YYYY-MM" or next')
parser.add_argument('-s', dest='source', action='store', choices=('mcd64a1',),
                    required=True, help='Choose source')

args = parser.parse_args()
downloadDate = args.date

######
import logging

log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
if int(cfg.get('log', 'logging_streaming')) == 1:
    fh = logging.FileHandler(cfg.get('log', 'logging_file'))
else:
    fh = logging.StreamHandler()

fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

if downloadDate == 'next':
    # get the last item
    last_burned_area = BurnedArea.objects.order_by('date').last()
    next_date = last_burned_area.date + relativedelta(months=1)
    downloadDate = next_date.strftime('%Y-%m')
    print("Next month item is: ", downloadDate)

if len(downloadDate.split('-')) != 2:
    log.error('date is in the wrong format: %s' % downloadDate)
    sys.exit()

log.info('---- new batch of BURNED AREA ----')
log.info('processing date: %s' % downloadDate)

downloadDateArr = downloadDate.split('-')
ba_date = date(int(downloadDateArr[0]), int(downloadDateArr[1]), 1)

# check if exists
if BurnedArea.objects.filter(slug=ba_date.strftime("%Y-%m")).first():
    print('Burned area already exists!')
    log.info('Burned area already exists!')
    sys.exit()

# generating the filename - it uses julian date, 2013-06-03 = 154
try:
    julianDay = ba_date.strftime('%j')
except Exception as e:
    log.error('converting julian date from %s ' % downloadDateArr)
    log.error(e)
    sys.exit()

def fix_zeros(value, digits):
    if digits == 2:
        return '0' + str(value) if len(str(value)) < 2 else str(value)
    if digits == 3:
        return '00' + str(value) if len(str(value)) == 1 else ('0' + str(value) if len(str(value)) == 2 else str(value))

remoteFilename = f"MCD64monthly.A{downloadDateArr[0]}{fix_zeros(julianDay, 3)}.Win05.006.burndate.shapefiles.tar.gz"
localFilename = cfg.get(args.source, 'local_path') + remoteFilename

for attempt in range(4):
    url = cfg.get(args.source, 'host') + ":" + cfg.get(args.source, 'remote_path') + f"/{downloadDateArr[0]}/" + remoteFilename
    log.info('download started:  ' + url)
    # download with wget
    sftp_cmd = "sftp fire@" + url + " " + cfg.get(args.source, 'local_path')
    sftp_status = os.system(sftp_cmd)
    # TODO: check time for wget process
    # check wget_status
    if sftp_status == 0:
        log.info('download finished: ' + localFilename)
        break
    else:
        # if wget_status =! 0 is due a some error
        log.info("attempt " + str(attempt) + ': error downloading: ' + url)
        sleep(120)

##### extract
shutil.unpack_archive(localFilename, cfg.get(args.source, 'local_path'))

##### dissolve geometries
import geopandas as gpd
from shapely.geometry.multipolygon import MultiPolygon

burned_area_file = localFilename.replace(".shapefiles.tar.gz", ".shp")
f_in = gpd.read_file(burned_area_file)
f_dissolve = gpd.geoseries.GeoSeries(MultiPolygon([geom for geom in f_in.unary_union.geoms]))
f_dissolve.crs = f_in.crs
df_clip = gpd.clip(f_dissolve, gpd.read_file("../shapes/Colombia.shp"))

for f in glob.glob(burned_area_file.replace(".shp", "*")):
    os.remove(f)
df_clip.to_file(burned_area_file)

###########################################################################
# import active fires to databases
from page.data.burned_area.import_burned_area import from_source

from_source(args.source.upper(), burned_area_file, ba_date)

print('DONE')
