#!/usr/bin/python
#
# use:
#  python download_points_from_modis.py -i test -d "2014-12-04"

import sys, os

######
from configparser import ConfigParser
cfg = ConfigParser()
cfg.read(os.path.join('donwload_config.ini'))

######
import argparse

parser = argparse.ArgumentParser(description='Import fire points from FIRMS FTP and load into ArcGIS')
parser.add_argument('-d', dest='date', action='store', required=True,
                    help='Day to run the process format: YYYY/MM/DD or "yesterday"')
parser.add_argument('-s', dest='source', action='store', choices=('modis', 'viirs'), required=True,
                    help='Day to run the process format: YYYY/MM/DD or "yesterday"')

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

##### Testing date arguments
from datetime import date, timedelta, datetime

if downloadDate == 'yesterday':
    yesterday = date.today() - timedelta(1)
    downloadDate = yesterday.strftime('%Y-%m-%d')

if len(downloadDate.split('-')) != 3:
    log.error('date is in the wrong format: %s' % downloadDate)
    sys.exit()

log.info('---- new batch of FIRMS points ----')
log.info('processing date: %s' % downloadDate)

downloadDateArr = downloadDate.split('-')

#### FTP
import ftplib

# open FTP connection
try:
    ftp_host = cfg.get(args.source, 'ftp_host')
    ftp_username = cfg.get(args.source, 'ftp_username')
    ftp_password = cfg.get(args.source, 'ftp_password')
    # if is empty get from environment variables of OS
    if ftp_username == "":
        ftp_username = os.environ.get("ftp_username", '')
    if ftp_password == "":
        ftp_password = os.environ.get("ftp_password", '')
    tmp_file = ftplib.FTP(ftp_host, ftp_username, ftp_password)
except Exception as e:
    log.error('cannot login to ftp: %s' % cfg.get(args.source, 'ftp_host'))
    log.error(e)
    sys.exit()

log.info('connected to ftp: %s' % cfg.get(args.source, 'ftp_host'))

# changing directory
try:
    tmp_file.cwd(cfg.get(args.source, 'ftp_remote_path'))
except Exception as e:
    tmp_file.quit()
    log.error('cannot CD to %s ' % cfg.get(args.source, 'ftp_remote_path'))
    log.error(e)
    sys.exit()

log.info('CD to %s ' % cfg.get(args.source, 'ftp_remote_path'))

# generating the filename - it uses julian date, 2013-06-03 = 154
try:
    julianDay = date(int(downloadDateArr[0]), int(downloadDateArr[1]), int(downloadDateArr[2])).strftime('%j')
except Exception as e:
    tmp_file.quit()
    log.error('converting julian date from %s ' % downloadDateArr)
    log.error(e)
    sys.exit()

log.debug('Julian day since begin of the year: %s' % julianDay)

remoteFilename = cfg.get(args.source, 'ftp_basename') + downloadDateArr[0] + julianDay + '.txt'
log.info('remote filename: %s' % remoteFilename)

localFilename = cfg.get(args.source, 'ftp_local_path') + remoteFilename
log.info('local filename: %s' % localFilename)

# check if the file exists on the FTP site
try:
    fileSize = tmp_file.size(remoteFilename)
except Exception as e:
    tmp_file.quit()
    log.error('File doesnt exist in the FTP: ' + remoteFilename)
    log.error(e)
    sys.exit()

# downloading file
try:
    tmp_file.retrbinary('RETR %s' % remoteFilename, open(localFilename, 'wb').write)
except Exception as e:
    # os.unlink(localFilename)
    tmp_file.quit()
    log.error('cannot download: %s' % remoteFilename)
    log.error(e)
    sys.exit()

log.info('donwloaded: %s' % remoteFilename)
tmp_file.quit()
log.info('closing connection to ftp')

log.info('summary')
log.info('today date: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
log.info('processing date: %s' % downloadDate)
log.info('total points imported %s' % (downloadDate))

###########################################################################
# import active fires to databases

dir_file = os.path.abspath(os.curdir)
tmp_file = open('tmp_import.py', 'w')

tmp_file.write('import os\n')
tmp_file.write('from page.data.active_fires.import_active_fires import modis\n')
tmp_file.write('from django.conf import settings\n')

if args.source == 'modis':
    tmp_file.write("modis(os.path.join(settings.BASE_DIR, 'page', 'data', "
            "'active_fires', 'modis', 'files', '{0}'))\n".format(remoteFilename))

if args.source == 'viirs':
    tmp_file.write("modis(os.path.join(settings.BASE_DIR, 'page', 'data', "
            "'active_fires', 'modis', 'files', '{0}'))\n".format(remoteFilename))


os.chdir("..")
os.chdir("..")
os.chdir("..")
tmp_file.close()

return_code = os.popen("/usr/bin/python3 manage.py shell < page/data/active_fires/tmp_import.py")
[print(i) for i in return_code]

os.remove('page/data/active_fires/tmp_import.py')
print("\nDONE")
