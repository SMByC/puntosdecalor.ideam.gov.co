#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Fill a local database with demo data so the page can be opened and exercised
without a copy of the production database.

    python manage.py seed_demo_data

The geometries are ROUGH APPROXIMATIONS (bounding boxes and a simplified
country outline) meant only to make the map, the region drop-list, the spatial
filter and the burned area layers work locally. They are not official
boundaries and must never be loaded into a production database.
"""

import random
from datetime import date, datetime, timedelta

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from page.models import ActiveFire, BurnedArea, Region

# Simplified outline of Colombia (lon, lat), used for the "colombia" region
COLOMBIA_OUTLINE = [
    (-71.1, 12.4), (-72.0, 11.7), (-73.5, 11.3), (-74.9, 11.1), (-75.6, 10.7),
    (-76.2, 9.4), (-77.4, 8.6), (-77.4, 7.9), (-77.2, 7.2), (-77.9, 7.5),
    (-78.1, 6.5), (-77.4, 4.0), (-77.9, 2.7), (-78.6, 2.5), (-79.0, 1.7),
    (-78.9, 1.4), (-77.7, 0.8), (-76.4, 0.4), (-75.3, -0.1), (-74.8, -0.6),
    (-73.7, -1.2), (-72.4, -2.4), (-71.5, -2.2), (-70.1, -2.6), (-70.0, -4.2),
    (-69.6, -4.2), (-69.4, -1.1), (-69.9, -0.6), (-69.6, 1.1), (-69.8, 1.7),
    (-67.3, 2.0), (-67.1, 1.2), (-66.9, 1.2), (-66.9, 1.9), (-67.8, 2.8),
    (-67.4, 3.7), (-67.9, 4.5), (-67.5, 5.5), (-67.8, 6.3), (-69.4, 6.1),
    (-70.1, 6.9), (-71.0, 6.9), (-72.0, 7.0), (-72.5, 7.5), (-72.4, 8.4),
    (-72.9, 9.1), (-72.7, 9.9), (-72.2, 11.1), (-71.3, 11.8), (-71.1, 12.4),
]

# name -> (lon_min, lat_min, lon_max, lat_max), approximate extents
DEPARTAMENTOS = {
    "Amazonas": (-73.8, -4.2, -69.4, -0.5),
    "Antioquia": (-77.1, 5.4, -73.9, 8.9),
    "Caquetá": (-76.4, -0.5, -71.0, 2.9),
    "Cundinamarca": (-75.0, 3.7, -73.0, 5.8),
    "Guaviare": (-73.9, 0.6, -69.5, 2.9),
    "Meta": (-75.0, 1.6, -71.1, 4.9),
    "Nariño": (-79.0, 0.3, -76.6, 2.7),
    "Putumayo": (-77.3, -1.0, -73.5, 1.4),
    "Santander": (-74.6, 5.7, -72.5, 8.1),
    "Vichada": (-71.5, 2.5, -67.4, 6.4),
}

REGIONES_NATURALES = {
    "Amazonía": (-79.0, -4.3, -66.8, 2.5),
    "Andina": (-77.5, 1.0, -72.0, 8.5),
    "Caribe": (-77.5, 8.0, -71.0, 12.6),
    "Orinoquía": (-73.5, 1.5, -67.0, 7.1),
    "Pacífica": (-79.1, 1.4, -76.0, 8.7),
}

PARQUES_NACIONALES = {
    "PNN Serranía de Chiribiquete": (-74.5, 0.0, -72.0, 2.2),
    "PNN Sierra de La Macarena": (-74.2, 2.2, -73.5, 3.6),
    "PNN Tinigua": (-74.4, 2.2, -74.0, 3.0),
    "PNN Amacayacu": (-70.5, -3.9, -69.8, -3.0),
    "PNN Tayrona": (-74.2, 11.2, -73.9, 11.4),
}

CORPORACIONES = {
    "CORPOAMAZONIA": (-77.3, -4.2, -71.0, 1.5),
    "CORMACARENA": (-75.0, 1.6, -71.1, 4.9),
    "CDA": (-73.9, -0.5, -67.0, 3.0),
    "CORANTIOQUIA": (-77.1, 5.4, -73.9, 8.9),
    "CORPORINOQUIA": (-73.5, 2.5, -67.4, 7.1),
}

# where the demo hotspots concentrate: (lon, lat, weight)
HOTSPOT_CENTERS = [
    (-74.5, 2.2, 5),   # arco de deforestación, Caquetá/Meta
    (-73.2, 1.5, 4),   # Guaviare
    (-75.3, 1.0, 3),   # Caquetá
    (-71.5, 4.5, 4),   # sabanas de Vichada/Meta
    (-73.0, 3.5, 3),   # Meta
    (-70.0, 5.5, 2),   # Vichada
    (-75.5, 6.5, 1),   # Antioquia
    (-73.5, 8.0, 1),   # Magdalena medio
]

SOURCES = [
    (ActiveFire.Source.VIIRS_SUOMI_NPP, 0.30),
    (ActiveFire.Source.VIIRS_NOAA_20, 0.28),
    (ActiveFire.Source.VIIRS_NOAA_21, 0.17),
    (ActiveFire.Source.MODIS_AQUA, 0.13),
    (ActiveFire.Source.MODIS_TERRA, 0.12),
]


def box(lon_min, lat_min, lon_max, lat_max):
    """Rectangular MultiPolygon for the given extent."""
    ring = (
        (lon_min, lat_min), (lon_max, lat_min), (lon_max, lat_max),
        (lon_min, lat_max), (lon_min, lat_min),
    )
    return MultiPolygon(Polygon(ring), srid=4326)


class Command(BaseCommand):
    help = "Fill the local database with demo regions, hotspots and burned areas."

    def add_arguments(self, parser):
        parser.add_argument('--fires', type=int, default=4000,
                            help="number of demo hotspots to create (default: 4000)")
        parser.add_argument('--days', type=int, default=30,
                            help="spread the hotspots over the last N days (default: 30)")
        parser.add_argument('--months', type=int, default=24,
                            help="number of monthly burned area layers (default: 24)")
        parser.add_argument('--seed', type=int, default=20260813,
                            help="random seed, for reproducible demo data")
        parser.add_argument('--keep', action='store_true',
                            help="add to the existing data instead of replacing it")

    def handle(self, *args, **options):
        from django.conf import settings

        engine = settings.DATABASES['default']['ENGINE']
        if 'spatialite' not in engine:
            raise CommandError(
                f"Refusing to write demo data through the '{engine}' backend: this command is "
                "only for the local SQLite/SpatiaLite database "
                "(DJANGO_SETTINGS_MODULE=active_fires.settings_local)."
            )

        random.seed(options['seed'])

        with transaction.atomic():
            if not options['keep']:
                self.stdout.write("Deleting previous demo data…")
                ActiveFire.objects.all().delete()
                BurnedArea.objects.all().delete()
                Region.objects.all().delete()

            regions = self.seed_regions()
            fires = self.seed_active_fires(options['fires'], options['days'])
            burned = self.seed_burned_areas(options['months'])

        self.seed_downloadable_files()

        self.stdout.write(self.style.SUCCESS(
            f"\nDemo data ready: {regions} regiones, {fires} puntos de calor, "
            f"{burned} meses de área quemada."
        ))
        self.stdout.write(self.style.WARNING(
            "The geometries are rough approximations for local testing only."
        ))

    # -- regions -------------------------------------------------------------

    def seed_regions(self):
        regions = [Region(
            name="Colombia",
            slug="colombia",
            group=None,
            shape=MultiPolygon(Polygon(tuple(COLOMBIA_OUTLINE)), srid=4326),
        )]

        for group, extents in (
            (Region.Group.DEPARTAMENTOS, DEPARTAMENTOS),
            (Region.Group.REGIONES_NATURALES, REGIONES_NATURALES),
            (Region.Group.PARQUES_NACIONALES, PARQUES_NACIONALES),
            (Region.Group.CORPORACIONES, CORPORACIONES),
        ):
            for name, extent in extents.items():
                regions.append(Region(
                    name=name,
                    slug=slugify(name),
                    group=group,
                    shape=box(*extent),
                ))

        Region.objects.bulk_create(regions)
        self.stdout.write(f"  regiones .......... {len(regions)}")
        return len(regions)

    # -- active fires --------------------------------------------------------

    def seed_active_fires(self, count, days):
        sources = [s for s, _ in SOURCES]
        weights = [w for _, w in SOURCES]
        centers = [(lon, lat) for lon, lat, weight in HOTSPOT_CENTERS for _ in range(weight)]

        now = datetime.now().replace(microsecond=0)
        fires = []

        for _ in range(count):
            lon, lat = random.choice(centers)
            lon += random.gauss(0, 0.35)
            lat += random.gauss(0, 0.35)

            source = random.choices(sources, weights=weights)[0]
            is_modis = source.startswith('MODIS')
            when = now - timedelta(
                days=random.uniform(0, days), hours=random.uniform(0, 24)
            )
            day_night = ActiveFire.DayNight.DAY if 6 <= when.hour <= 18 else ActiveFire.DayNight.NIGHT

            fires.append(ActiveFire(
                geom=Point(round(lon, 5), round(lat, 5), srid=4326),
                date=when,
                source=source,
                brightness=round(random.uniform(300, 420), 1),
                brightness_alt=round(random.uniform(280, 320), 1),
                confidence=(str(random.randint(30, 100)) if is_modis
                            else random.choice(['baja', 'nominal', 'alta'])),
                frp=round(random.uniform(0.5, 90), 1),
                day_night=day_night,
                scan=round(random.uniform(0.375, 2.5), 2),
                track=round(random.uniform(0.375, 1.6), 2),
            ))

        ActiveFire.objects.bulk_create(fires, batch_size=1000)
        self.stdout.write(f"  puntos de calor ... {len(fires)} (últimos {days} días)")
        return len(fires)

    # -- burned areas --------------------------------------------------------

    def seed_burned_areas(self, months):
        today = date.today()
        year, month = today.year, today.month
        created = 0

        for _ in range(months):
            month -= 1
            if month == 0:
                year, month = year - 1, 12

            polygons = []
            for _ in range(random.randint(8, 18)):
                lon, lat = random.choice([(c[0], c[1]) for c in HOTSPOT_CENTERS])
                lon += random.gauss(0, 0.5)
                lat += random.gauss(0, 0.5)
                size = random.uniform(0.04, 0.22)
                polygons.append(Polygon((
                    (lon, lat), (lon + size, lat), (lon + size, lat + size),
                    (lon, lat + size), (lon, lat),
                )))

            BurnedArea.objects.create(
                date=date(year, month, 1),
                slug=f"{year}-{month:02d}",
                source=BurnedArea.Source.MCD64A1,
                shape=MultiPolygon(polygons, srid=4326),
            )
            created += 1

        self.stdout.write(f"  área quemada ...... {created} meses")
        return created

    # -- files listed by the "archivos" pages --------------------------------

    def seed_downloadable_files(self):
        """A few sample files so /archivos-csv/ and /archivos-area-quemada/ are
        not empty. Existing directories are left untouched."""
        import zipfile
        from django.conf import settings

        csv_dir = settings.BASE_DIR / 'page' / 'data' / 'ftp_files'
        zip_dir = settings.BASE_DIR / 'page' / 'data' / 'ftp_ba_files'

        if csv_dir.exists() or zip_dir.exists():
            self.stdout.write("  archivos .......... ya existen, sin cambios")
            return

        csv_dir.mkdir(parents=True, exist_ok=True)
        zip_dir.mkdir(parents=True, exist_ok=True)

        header = ("Fecha (UTC-5);Lat;Lon;Fuente;Temperatura (C);Temperatura Alt* (C);"
                  "Radiación térmica (MW);Confianza;Captura (Dia-Noche);"
                  "Scan - real pixel size (km);Track - real pixel size (km)\n")

        def comma(value):
            """Decimal separator used by the published files."""
            return '' if value is None else str(value).replace('.', ',')

        for days_ago in range(3):
            day = date.today() - timedelta(days=days_ago)
            rows = [header]
            for fire in ActiveFire.objects.filter(date__date=day)[:40]:
                rows.append(";".join([
                    f"{fire.date:%Y-%m-%d %H:%M}",
                    comma(round(fire.geom.y, 5)), comma(round(fire.geom.x, 5)),
                    fire.source,
                    comma(round(fire.brightness - 273.15, 1)),
                    comma(round(fire.brightness_alt - 273.15, 1) if fire.brightness_alt else None),
                    comma(fire.frp), fire.confidence or '', fire.day_night or '',
                    comma(fire.scan), comma(fire.track),
                ]) + "\n")
            (csv_dir / f"puntos_de_calor_{day:%Y-%m-%d}.csv").write_text("".join(rows), encoding="utf-8")

        for burned_area in BurnedArea.objects.all()[:3]:
            with zipfile.ZipFile(zip_dir / f"MCD64A1_{burned_area.slug}.zip", "w") as archive:
                archive.writestr(
                    f"MCD64A1_{burned_area.slug}.txt",
                    "Archivo de demostración generado por seed_demo_data.\n"
                    "En producción aquí va el shapefile comprimido del área quemada.\n",
                )

        self.stdout.write("  archivos .......... 3 csv + 3 zip de ejemplo")
