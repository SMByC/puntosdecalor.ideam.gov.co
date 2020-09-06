#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

# use:
#
# cd /home/activefires/apps/Active_Fires/page/data/active_fires
#  python3.8 download_active_fires.py -s modis -d "2014-12-04"
#  python3.8 download_active_fires.py -s viirs -d "2014-12-04"

import sys, os
from time import sleep
from datetime import date, timedelta

os.chdir(os.path.dirname(os.path.realpath(__file__)))

######
from configparser import ConfigParser
cfg = ConfigParser()
cfg.read(os.path.join('donwload_config.ini'))

######
import argparse

parser = argparse.ArgumentParser(description='Import fire points from FIRMS FTP and load into Active_Fires database')
parser.add_argument('-d', dest='date', action='store', required=True,
                    help='Day to run the process format: "YYYY-MM-DD" or "yesterday"')
parser.add_argument('-s', dest='source', action='store', choices=('modis', 'viirs'), required=True,
                    help='Choose source')

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


if downloadDate == 'yesterday':
    yesterday = date.today() - timedelta(1)
    downloadDate = yesterday.strftime('%Y-%m-%d')

if len(downloadDate.split('-')) != 3:
    log.error('date is in the wrong format: %s' % downloadDate)
    sys.exit()

log.info('---- new batch of FIRMS points ----')
log.info('processing date: %s' % downloadDate)

downloadDateArr = downloadDate.split('-')

# generating the filename - it uses julian date, 2013-06-03 = 154
try:
    julianDay = date(int(downloadDateArr[0]), int(downloadDateArr[1]), int(downloadDateArr[2])).strftime('%j')
except Exception as e:
    log.error('converting julian date from %s ' % downloadDateArr)
    log.error(e)
    sys.exit()

remoteFilename = cfg.get(args.source, 'basename') + downloadDateArr[0] + julianDay + '.txt'
localFilename = cfg.get(args.source, 'local_path') + remoteFilename

for attempt in range(10):
    url = cfg.get(args.source, 'host') + cfg.get(args.source, 'remote_path') + remoteFilename
    log.info('download started:  ' + url)
    # download with wget
    app_key = os.environ.get("app_key", '')
    wget_cmd = "wget -e robots=off -m -np -R .html,.tmp -nH -nd --header" \
               " \"Authorization: Bearer {}\" ".format(app_key) + url + " -P " + cfg.get(args.source, 'local_path')
    wget_status = os.system(wget_cmd)
    # TODO: check time for wget process
    # check wget_status
    if wget_status == 0:
        log.info('download finished: ' + localFilename)
        break
    else:
        # if wget_status =! 0 is due a some error
        log.info("attempt " + str(attempt) + ': error downloading: ' + url)
        sleep(120)

###########################################################################
# import active fires to databases

dir_file = os.path.abspath(os.curdir)
tmp_file = open('tmp_import.py', 'w')

tmp_file.write('import os\n')
tmp_file.write('from page.data.active_fires.import_active_fires import from_source\n')
tmp_file.write('from django.conf import settings\n')

tmp_file.write("from_source('{source}', os.path.join(settings.BASE_DIR, 'page', 'data', "
               "'active_fires', '{source}', 'files', '{filename}'))\n"
               .format(source=args.source, filename=remoteFilename))

os.chdir("..")
os.chdir("..")
os.chdir("..")
tmp_file.close()

return_code = os.popen("/usr/local/bin/python3.8 manage.py shell < page/data/active_fires/tmp_import.py")
[print(i) for i in return_code]

os.remove('page/data/active_fires/tmp_import.py')
log.info("\nDONE")
