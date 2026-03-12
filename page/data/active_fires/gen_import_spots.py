#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

# use:
#
# cd /home/activefires/apps/Active_Fires/page/data/active_fires
# python gen_import_spots.py
# bash import.sh


import pandas as pd


date_range = pd.date_range("2022-09-07", "2022-11-05", freq="D")

f = open('import.sh', 'w')
for date_import in date_range:

    f.write("python download_active_fires.py -s modis -d \"{}\"\n".format(date_import.strftime("%Y-%m-%d")))
    f.write("python download_active_fires.py -s viirs-noaa-20 -d \"{}\"\n".format(date_import.strftime("%Y-%m-%d")))
    f.write("python download_active_fires.py -s viirs-noaa-21 -d \"{}\"\n".format(date_import.strftime("%Y-%m-%d")))
    f.write("python download_active_fires.py -s viirs-suomi-npp -d \"{}\"\n".format(date_import.strftime("%Y-%m-%d")))

f.close()
