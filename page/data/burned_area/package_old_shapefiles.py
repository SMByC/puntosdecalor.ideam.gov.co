#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Temporary script to compress all existing burned area shapefiles
# into zip files stored in page/data/ftp_ba_files/.
#
# Usage:
#   cd /home/activefires/apps/Active_Fires
#   python page/data/burned_area/package_old_shapefiles.py
#
# Safe to delete after running.

import re
import zipfile
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[2]
FILES_DIR = SCRIPT_DIR / 'mcd64a1' / 'files'
FTP_DIR = PROJECT_DIR / 'page' / 'data' / 'ftp_ba_files'

SHP_EXTENSIONS = ('.shp', '.shx', '.dbf', '.prj', '.cpg')
FILENAME_PATTERN = re.compile(r'MCD64monthly\.A(\d{4})(\d{3})\.')


def julian_to_date(year, julian_day):
    return date(year, 1, 1) + timedelta(days=julian_day - 1)


def main():
    FTP_DIR.mkdir(parents=True, exist_ok=True)

    shp_files = sorted(FILES_DIR.glob('*.shp'))
    if not shp_files:
        print(f"No .shp files found in {FILES_DIR}")
        return

    print(f"Found {len(shp_files)} shapefile(s) in {FILES_DIR}\n")

    for shp in shp_files:
        match = FILENAME_PATTERN.match(shp.name)
        if not match:
            print(f"  SKIP: {shp.name} (filename does not match expected pattern)")
            continue

        ba_date = julian_to_date(int(match.group(1)), int(match.group(2)))
        zip_name = f"Area_quemada_Colombia_{ba_date.strftime('%Y-%m')}.zip"
        zip_path = FTP_DIR / zip_name

        if zip_path.exists():
            print(f"  SKIP: {zip_name} already exists")
            continue

        components = [f for f in shp.parent.glob(f"{shp.stem}.*")
                      if f.suffix.lower() in SHP_EXTENSIONS]

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in components:
                zf.write(f, f.name)

        print(f"  OK: {zip_name}  ({len(components)} files, date: {ba_date.strftime('%Y-%m')})")

    print(f"\nDone. Zip files stored in {FTP_DIR}")


if __name__ == '__main__':
    main()
