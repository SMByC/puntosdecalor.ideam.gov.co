#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2020-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

# Usage:
#
# cd /home/activefires/apps/Active_Fires/page/data/burned_area
#  python download_burned_area.py -s mcd64a1 -d 2020-1
#  python download_burned_area.py -s mcd64a1 -d next
#
# DATA SOURCES:
# https://modis-fire.umd.edu/index.html

import argparse
import logging
import os
import shutil
import subprocess
import sys
from configparser import ConfigParser
from datetime import date
from pathlib import Path
from time import sleep

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[2]
SHAPES_DIR = SCRIPT_DIR.parent / 'shapes'

SOURCES = ('mcd64a1',)
MAX_DOWNLOAD_ATTEMPTS = 4


def setup_django():
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "active_fires.settings")

    import django
    django.setup()


def setup_logging(cfg):
    log = logging.getLogger("download_burned_area")
    log.setLevel(logging.DEBUG)

    if log.handlers:
        return log

    if int(cfg.get('log', 'logging_streaming')) == 1:
        handler = logging.FileHandler(SCRIPT_DIR / cfg.get('log', 'logging_file'))
    else:
        handler = logging.StreamHandler()

    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download burned area from MCD64A1 and import into database'
    )
    parser.add_argument(
        '-d', dest='date', required=True,
        help='Month to process: "YYYY-MM" or "next" (auto-detect next month)',
    )
    parser.add_argument(
        '-s', dest='source', choices=SOURCES, required=True,
        help='Data source',
    )
    return parser.parse_args()


def resolve_date(date_str, log):
    """Resolve the date argument into a date object (first day of month).

    Supports 'next' to automatically pick the month after the last imported entry.
    """
    from page.models import BurnedArea

    if date_str == 'next':
        from dateutil.relativedelta import relativedelta
        last_burned_area = BurnedArea.objects.order_by('date').last()
        if last_burned_area is None:
            log.error("No existing burned area entries found, cannot determine 'next'")
            return None
        next_date = last_burned_area.date + relativedelta(months=1)
        log.info(f"Next month item is: {next_date.strftime('%Y-%m')}")
        return next_date

    parts = date_str.split('-')
    if len(parts) != 2:
        return None

    try:
        return date(int(parts[0]), int(parts[1]), 1)
    except (ValueError, IndexError):
        return None


def download_file(url, dest_dir, sftp_password, log):
    """Download a file via sftp using sshpass. Returns True on success."""
    cmd = [
        "sshpass", "-p", sftp_password,
        "sftp", f"fire@{url}", str(dest_dir),
    ]

    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        log.info(f"Download attempt {attempt}/{MAX_DOWNLOAD_ATTEMPTS}: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            log.info(f"Download successful: {url}")
            return True

        log.warning(f"Attempt {attempt} failed (exit code {result.returncode})")
        if result.stderr:
            log.debug(f"sftp stderr: {result.stderr[:500]}")

        if attempt < MAX_DOWNLOAD_ATTEMPTS:
            sleep(120)

    return False


def dissolve_and_clip(burned_area_shp, log):
    """Dissolve all burn polygons into a single MultiPolygon and clip to Colombia."""
    import geopandas as gpd
    from shapely.geometry import MultiPolygon

    log.info(f"Dissolving and clipping: {burned_area_shp}")

    colombia_shp = SHAPES_DIR / 'Colombia.shp'
    f_in = gpd.read_file(burned_area_shp)
    dissolved = gpd.GeoSeries(
        MultiPolygon([geom for geom in f_in.unary_union.geoms])
    )
    dissolved.crs = f_in.crs
    clipped = gpd.clip(dissolved, gpd.read_file(colombia_shp))

    for f in burned_area_shp.parent.glob(f"{burned_area_shp.stem}*"):
        f.unlink()
    clipped.to_file(burned_area_shp)

    log.info("Dissolve and clip completed")
    return burned_area_shp


def import_to_database(source, burned_area_shp, ba_date, log):
    """Import the processed shapefile into the database."""
    from page.data.burned_area.import_burned_area import from_source

    log.info(f"Importing {burned_area_shp} (source: {source}, date: {ba_date})")
    from_source(source.upper(), str(burned_area_shp), ba_date)
    log.info("Import finished")


def main():
    args = parse_args()

    cfg = ConfigParser()
    cfg.read(SCRIPT_DIR / 'donwload_config.ini')

    log = setup_logging(cfg)

    setup_django()

    from page.models import BurnedArea

    ba_date = resolve_date(args.date, log)
    if ba_date is None:
        log.error(f"Invalid date format: {args.date}")
        sys.exit(1)

    if BurnedArea.objects.filter(slug=ba_date.strftime("%Y-%m")).first():
        log.info(f"Burned area for {ba_date.strftime('%Y-%m')} already exists, skipping")
        sys.exit(0)

    log.info("---- new batch of BURNED AREA ----")
    log.info(f"Processing date: {ba_date.strftime('%Y-%m')}, source: {args.source}")

    julian_day = ba_date.strftime('%j').zfill(3)
    year = str(ba_date.year)

    remote_filename = f"MCD64monthly.A{year}{julian_day}.Win05.061.burndate.shapefiles.tar.gz"
    local_dir = SCRIPT_DIR / cfg.get(args.source, 'local_path')
    local_archive = local_dir / remote_filename

    local_dir.mkdir(parents=True, exist_ok=True)

    host = cfg.get(args.source, 'host')
    remote_path = cfg.get(args.source, 'remote_path')
    url = f"{host}:{remote_path}/{year}/{remote_filename}"

    sftp_password = os.environ.get("SFTP_PASSWORD", "burnt")

    if not download_file(url, local_dir, sftp_password, log):
        log.error(f"Failed to download after {MAX_DOWNLOAD_ATTEMPTS} attempts: {url}")
        sys.exit(1)

    if not local_archive.exists():
        log.error(f"Downloaded archive not found at: {local_archive}")
        sys.exit(1)

    log.info(f"Extracting: {local_archive}")
    shutil.unpack_archive(local_archive, local_dir)

    burned_area_shp = local_dir / remote_filename.replace(".shapefiles.tar.gz", ".shp")
    dissolve_and_clip(burned_area_shp, log)
    import_to_database(args.source, burned_area_shp, ba_date, log)

    log.info("DONE")


if __name__ == '__main__':
    main()
