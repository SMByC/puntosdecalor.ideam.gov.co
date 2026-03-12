#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

# Usage:
#
# cd /home/activefires/apps/Active_Fires/page/data/active_fires
#  python download_active_fires.py -s modis -d "2014-12-04"
#  python download_active_fires.py -s viirs-noaa-20 -d "2014-12-04"
#  python download_active_fires.py -s viirs-noaa-21 -d "2014-12-04"
#  python download_active_fires.py -s viirs-suomi-npp -d "2014-12-04"
#  python download_active_fires.py -s viirs-suomi-npp -d "yesterday"

import argparse
import logging
import os
import sys
from configparser import ConfigParser
from datetime import date, timedelta
from pathlib import Path
from time import sleep
from urllib.error import URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parents[2]

SOURCES = ('modis', 'viirs-noaa-20', 'viirs-noaa-21', 'viirs-suomi-npp')
MAX_DOWNLOAD_ATTEMPTS = 3


def setup_django():
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "active_fires.settings")

    import django
    django.setup()


def setup_logging(cfg):
    log = logging.getLogger("download_active_fires")
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
        description='Download fire points from FIRMS and import into Active_Fires database'
    )
    parser.add_argument(
        '-d', dest='date', required=True,
        help='Day to process: "YYYY-MM-DD" or "yesterday"',
    )
    parser.add_argument(
        '-s', dest='source', choices=SOURCES, required=True,
        help='Satellite source',
    )
    return parser.parse_args()


def resolve_date(date_str):
    if date_str == 'yesterday':
        return date.today() - timedelta(days=1)

    parts = date_str.split('-')
    if len(parts) != 3:
        return None

    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def download_file(url, dest_path, app_key, log):
    """Download a file via HTTPS with Bearer token auth. Returns True on success."""
    req = Request(url, headers={"Authorization": f"Bearer {app_key}"})

    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        log.info(f"Download attempt {attempt}/{MAX_DOWNLOAD_ATTEMPTS}: {url}")
        try:
            with urlopen(req, timeout=120) as response:
                dest_path.write_bytes(response.read())
            log.info(f"Download successful: {dest_path}")
            return True
        except URLError as e:
            log.warning(f"Attempt {attempt} failed: {e}")
        except OSError as e:
            log.warning(f"Attempt {attempt} I/O error: {e}")

        if attempt < MAX_DOWNLOAD_ATTEMPTS:
            sleep(5)

    return False


def import_to_database(source, csv_file, log):
    """Import downloaded CSV into the database via Django ORM."""
    from page.data.active_fires.import_active_fires import from_source

    log.info(f"Importing {csv_file} (source: {source})")
    from_source(source, str(csv_file))
    log.info("Import finished")


def main():
    args = parse_args()

    cfg = ConfigParser()
    cfg.read(SCRIPT_DIR / 'donwload_config.ini')

    log = setup_logging(cfg)

    download_date = resolve_date(args.date)
    if download_date is None:
        log.error(f"Invalid date format: {args.date}")
        sys.exit(1)

    log.info("---- new batch of FIRMS points ----")
    log.info(f"Processing date: {download_date.isoformat()}, source: {args.source}")

    julian_day = download_date.strftime('%j')
    year = str(download_date.year)

    remote_filename = cfg.get(args.source, 'basename') + year + julian_day + '.txt'
    local_dir = SCRIPT_DIR / cfg.get(args.source, 'local_path')
    local_file = local_dir / remote_filename

    local_dir.mkdir(parents=True, exist_ok=True)

    url = cfg.get(args.source, 'host') + cfg.get(args.source, 'remote_path') + remote_filename
    app_key = os.environ.get("app_key", '')

    if not download_file(url, local_file, app_key, log):
        log.error(f"Failed to download after {MAX_DOWNLOAD_ATTEMPTS} attempts: {url}")
        sys.exit(1)

    setup_django()
    import_to_database(args.source, local_file, log)

    log.info("DONE")


if __name__ == '__main__':
    main()
