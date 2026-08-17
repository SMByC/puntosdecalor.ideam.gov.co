#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Check that everything GeoDjango needs to run locally on SQLite is present:
the GEOS and GDAL system libraries, and the SpatiaLite extension of SQLite.

    python dev/preflight.py

Exits with 0 when the local stack is usable, 1 with install hints otherwise.
"""

import os
import sqlite3
import sys

HINTS = """
Install the missing system libraries:

  Arch/Manjaro     sudo pacman -S geos gdal libspatialite
  Debian/Ubuntu    sudo apt install libgeos-c1v5 gdal-bin libsqlite3-mod-spatialite
  Fedora           sudo dnf install geos gdal libspatialite
  macOS (brew)     brew install geos gdal libspatialite
                   then: export SPATIALITE_LIBRARY_PATH=$(brew --prefix)/lib/mod_spatialite.dylib
"""


def check_geos_gdal():
    """GeoDjango loads libgeos_c and libgdal through ctypes."""
    problems = []
    try:
        from django.contrib.gis.geos import GEOSGeometry
        GEOSGeometry("POINT(-74 4)")
        print("  GEOS ................. ok")
    except Exception as error:
        problems.append(f"GEOS not usable: {error}")
        print("  GEOS ................. MISSING")
    try:
        from django.contrib.gis.gdal import gdal_version
        print(f"  GDAL ................. ok ({gdal_version().decode(errors='ignore')})")
    except Exception as error:
        problems.append(f"GDAL not usable: {error}")
        print("  GDAL ................. MISSING")
    return problems


def check_spatialite():
    """The SQLite backend needs the mod_spatialite loadable extension.

    The names are tried in the same order as django's spatialite backend, so a
    green check here means `manage.py migrate` will find the library too.
    """
    from ctypes.util import find_library

    configured = os.environ.get("SPATIALITE_LIBRARY_PATH")
    # exactly what django.contrib.gis...spatialite.base builds
    django_candidates = [name for name in (
        configured, "mod_spatialite.so", "mod_spatialite", find_library("spatialite"),
    ) if name]
    # only reported as a hint, django would not try these by itself
    extra_candidates = ["mod_spatialite.dylib", "libspatialite.so", "libspatialite.dylib"]

    connection = sqlite3.connect(":memory:")
    try:
        connection.enable_load_extension(True)
    except AttributeError:
        print("  SpatiaLite ........... MISSING (python sqlite3 built without extension support)")
        return ["this python cannot load SQLite extensions "
                "(needs --enable-loadable-sqlite-extensions)"]

    def loads(name):
        try:
            connection.load_extension(name)
            return True
        except sqlite3.OperationalError:
            return False

    try:
        for candidate in django_candidates:
            if loads(candidate):
                print(f"  SpatiaLite ........... ok ({candidate})")
                return []

        # nothing django tries works: look for a library under another name so
        # the hint can be precise instead of "not found"
        for candidate in extra_candidates:
            if loads(candidate):
                print(f"  SpatiaLite ........... found as '{candidate}', but django will not try that name")
                return [f"export SPATIALITE_LIBRARY_PATH={candidate} (or add it to your shell profile), "
                        "django only probes " + ", ".join(repr(name) for name in django_candidates)]
    finally:
        connection.close()

    print("  SpatiaLite ........... MISSING")
    return ["mod_spatialite could not be loaded (tried "
            + ", ".join(repr(name) for name in django_candidates + extra_candidates) + ")"]


def main():
    print("Checking the local GIS stack:")
    problems = check_geos_gdal() + check_spatialite()

    if problems:
        print("\nCannot run locally yet:")
        for problem in problems:
            print(f"  - {problem}")
        print(HINTS)
        return 1

    print("\nEverything needed to run locally is available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
