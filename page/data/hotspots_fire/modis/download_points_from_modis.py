#!/usr/bin/python
# python download_points_from_modis.py -i test -d "2014-12-04"

import sys

######
from configparser import ConfigParser
import subprocess

cfg = ConfigParser()
cfg.read('download_points_from_modis.ini')

######
import argparse

parser = argparse.ArgumentParser(description='Import fire points from FIRMS FTP and load into ArcGIS')
parser.add_argument('-i', dest='serverInstance', action='store',choices={'test','production','dev'}, required=True, help='Server instance')
parser.add_argument('-d', dest='date', action='store', required=True, help='Day to run the process format: YYYY/MM/DD or "yesterday"')
args = parser.parse_args()

serverInstance = args.serverInstance
downloadDate = args.date

######
import logging

log = logging.getLogger(__file__)
log.setLevel(logging.DEBUG)
if int(cfg.get(serverInstance, 'logging_streaming')) == 1:		
	fh = logging.FileHandler(cfg.get(serverInstance, 'logging_file'))
else: 
	fh = logging.StreamHandler()

fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

##### Testing date arguments
import datetime
from datetime import date, timedelta, datetime
import time

if downloadDate == 'yesterday':
	yesterday = date.today() - timedelta(1)
	downloadDate = yesterday.strftime('%Y-%m-%d')

if len(downloadDate.split('-')) != 3:
	log.error('date is in the wrong format: %s' % downloadDate)	
	sys.exit()

log.info('---- new batch of FIRMS points ----')
log.info('processing date: %s' %  downloadDate)

downloadDateArr = downloadDate.split('-')

#### FTP
import ftplib
import os
import socket

# open FTP connection
try:
	f = ftplib.FTP(cfg.get(serverInstance, 'ftp_host'),cfg.get(serverInstance, 'ftp_username'), cfg.get(serverInstance, 'ftp_password'))
except Exception as e:
	log.error('cannot login to ftp: %s' % cfg.get(serverInstance, 'ftp_host'))
	log.error(e)
	sys.exit()

log.info('connected to ftp: %s' % cfg.get(serverInstance, 'ftp_host'))

#	changing directory
try:
	f.cwd(cfg.get(serverInstance, 'ftp_remote_path'))
except Exception as e:
	f.quit()
	log.error('cannot CD to %s ' % cfg.get(serverInstance, 'ftp_remote_path'))
	log.error(e)
	sys.exit()

log.info('CD to %s ' % cfg.get(serverInstance, 'ftp_remote_path'))

# generating the filename - it uses julian date, 2013-06-03 = 154
try:
	julianDay =  date(int(downloadDateArr[0]), int(downloadDateArr[1]), int(downloadDateArr[2])).strftime('%j')
except Exception as e:
	f.quit()
	log.error('converting julian date from %s ' % downloadDateArr)
	log.error(e)
	sys.exit()

log.debug('Julian day since begin of the year: %s' % julianDay)

remoteFilename = 'South_America_MCD14DL_'+ downloadDateArr[0] + julianDay +'.txt'
log.info('remote filename: %s' % remoteFilename)

localFilename = cfg.get(serverInstance, 'ftp_local_path') + remoteFilename
log.info('local filename: %s' % localFilename)

# check if the file exists on the FTP site
try:
	fileSize = f.size(remoteFilename)
except Exception as e:
	f.quit()
	log.error('File doesnt exist in the FTP: ' + remoteFilename)
	log.error(e)
	sys.exit()

# downloading file
try:
	f.retrbinary('RETR %s' % remoteFilename, open(localFilename, 'wb').write)
except Exception as e:
	# os.unlink(localFilename)
	f.quit()
	log.error('cannot download: %s' % remoteFilename)
	log.error(e)
	sys.exit()

log.info('donwloaded: %s' % remoteFilename)
f.quit()
log.info('closing connection to ftp')

#### Parsing from File to Array
log.info('parsing: %s' % localFilename)

fai_latitude   = int(cfg.get(serverInstance, 'fai_latitude'))
fai_longitude  = int(cfg.get(serverInstance, 'fai_longitude'))
fai_brightness = int(cfg.get(serverInstance, 'fai_brightness'))
fai_scan       = int(cfg.get(serverInstance, 'fai_scan'))
fai_track      = int(cfg.get(serverInstance, 'fai_track'))
fai_acq_date   = int(cfg.get(serverInstance, 'fai_acq_date'))
fai_acq_time   = int(cfg.get(serverInstance, 'fai_acq_time'))
fai_satellite  = int(cfg.get(serverInstance, 'fai_satellite'))
fai_confidence = int(cfg.get(serverInstance, 'fai_confidence'))
fai_version    = int(cfg.get(serverInstance, 'fai_version'))
fai_bright_t31 = int(cfg.get(serverInstance, 'fai_bright_t31'))
fai_frp        = int(cfg.get(serverInstance, 'fai_frp'))

f = open(localFilename,'r')
lstFires = f.readlines()
aFires = []

for fire in lstFires:
	lstValues = fire.split(',')

	if lstValues[0] == 'latitude':
		log.debug('skipping the file header: %s' % lstValues)
		continue

	zeroError = True
	try:		
		latitude   = float(lstValues[fai_latitude])
		longitude  = float(lstValues[fai_longitude])
		brightness = float(lstValues[fai_brightness])
		scan       = float(lstValues[fai_scan])
		track      = float(lstValues[fai_track])
		acq_date   = lstValues[fai_acq_date]
		acq_time   = lstValues[fai_acq_time]
		satellite  = lstValues[fai_satellite]
		confidence = int(lstValues[fai_confidence])
		version    = float(lstValues[fai_version])
		bright_t31 = float(lstValues[fai_bright_t31])
		frp        = float(lstValues[fai_frp].rstrip('\n'))
	except Exception as e:
		log.error('Error parsing: %s' % lstValues)
		log.error(e)
		zeroError = False

	if zeroError:		
		aFires.append([latitude, longitude, brightness, scan,track,acq_date,acq_time,satellite,confidence,version,bright_t31,frp])

f.close()

log.info('numero of points parsed to an array: %s'  % len(aFires))

	
log.info('summary')
log.info('today date: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
log.info('processing date: %s' %  downloadDate)
log.info('total points imported %s' % (downloadDate))




###########################################################################

os.chdir("..")
dir_file = os.path.abspath(os.curdir)
f = open('tmp_import.py','w')

f.write('import os\n')
f.write('from page.data.hotspots_fire.import_hotspots import modis\n')
f.write('from django.conf import settings\n')

f.write("modis(os.path.join(settings.BASE_DIR, 'page', 'data', 'hotspots_fire', 'modis', 'files', '{0}'))\n".format(remoteFilename))

os.chdir("..")
os.chdir("..")
os.chdir("..")
f.close()

#os.system("./manage.py shell < page/data/hotspots_fire/tmp_import.py")
#return_code = subprocess.call("/usr/bin/python3 manage.py shell < page/data/hotspots_fire/tmp_import.py", shell=True)
c=os.popen("/usr/bin/python3 manage.py shell < page/data/hotspots_fire/tmp_import.py")
[print(i) for i in c]








