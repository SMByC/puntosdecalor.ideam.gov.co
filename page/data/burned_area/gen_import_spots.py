#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2020
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

import pandas as pd


date_range = pd.date_range("2019-01-01", "2020-10-01", freq="M")

f = open('import.sh', 'w')
for date_import in date_range:
    f.write("python3.8 download_burned_area.py -s mcd64a1 -d \"{}\"\n".format(date_import.strftime("%Y-%m")))

f.close()