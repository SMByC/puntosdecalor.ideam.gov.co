#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

# use:
#
# cd /home/activefires/apps/Active_Fires/page/data/active_fires
# bash import.sh


import pandas as pd


date_range = pd.date_range("2016-01-01", "2017-08-15", freq="D")

f = open('import.sh', 'w')
for date_import in date_range:

    f.write("python3.7 download_active_fires.py -s modis -d \"{}\"\n".format(date_import.strftime("%Y-%m-%d")))
    f.write("python3.7 download_active_fires.py -s viirs -d \"{}\"\n".format(date_import.strftime("%Y-%m-%d")))

f.close()