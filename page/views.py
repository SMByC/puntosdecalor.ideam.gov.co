#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

import csv
import logging
from datetime import datetime, date, timedelta
from urllib.parse import urlencode, urlparse, parse_qs

from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from djgeojson.views import GeoJSONLayerView

from page.models import ActiveFire, Region, BurnedArea

logger = logging.getLogger(__name__)


# -- GeoJSON API views -------------------------------------------------------

class RegionMapLayer(GeoJSONLayerView):
    model = Region
    geometry_field = 'shape'
    properties = ('name',)

    def get_queryset(self):
        region_slug = self.request.GET.get('region')
        if region_slug:
            return Region.objects.filter(slug=region_slug)
        return Region.objects.none()


class BurnedAreaMapLayer(GeoJSONLayerView):
    model = BurnedArea
    geometry_field = 'shape'
    properties = ('slug',)

    def get_queryset(self):
        date_str = self.request.GET.get('date')
        if date_str:
            parts = date_str.split("-")
            ba_date = date(int(parts[0]), int(parts[1]), 1)
            return BurnedArea.objects.filter(date=ba_date)
        return BurnedArea.objects.none()


class ActiveFiresMapLayer(GeoJSONLayerView):
    model = ActiveFire
    properties = ('id',)

    def get_queryset(self):
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')
        region_slug = self.request.GET.get('region')

        if not all([from_date, to_date, region_slug]):
            return ActiveFire.objects.none()

        return _filter_active_fires(from_date, to_date, region_slug)


# -- Shared query helpers ----------------------------------------------------

def _parse_date_range(from_date_str, to_date_str):
    """Parse date strings into a (from_datetime, to_datetime) covering the full day range."""
    from_dt = datetime.strptime(from_date_str, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    return from_dt, to_dt


def _filter_active_fires(from_date_str, to_date_str, region_slug):
    """Return an ActiveFire queryset filtered by date range and optional region."""
    from_dt, to_dt = _parse_date_range(from_date_str, to_date_str)
    qs = ActiveFire.objects.filter(date__gte=from_dt, date__lte=to_dt)
    if region_slug != "colombia":
        region = Region.objects.get(slug=region_slug)
        qs = qs.filter(geom__within=region.shape)
    return qs


# -- DEM elevation lookup (lazy-loaded) --------------------------------------

_UNTRIED = object()
_dem_xarr = _UNTRIED


def _get_dem():
    """Open the DEM once. Returns None when it is not available (the raster is
    not part of the repository, so local/dev setups usually do not have it).

    A raster that cannot be opened (missing file, rioxarray not installed --
    RasterioIOError derives from OSError) is remembered, since retrying would
    only repeat the same failure on every popup; any other error is retried on
    the next request so a transient one does not disable the elevation until
    the worker is restarted."""
    global _dem_xarr
    if _dem_xarr is _UNTRIED:
        try:
            import rioxarray
            _dem_xarr = rioxarray.open_rasterio(settings.BASE_DIR / "static" / "dem" / "DEM_COL.img")
        except (OSError, ImportError):
            logger.warning(
                "DEM not available (not retried until restart), the elevation "
                "will not be reported in the popups",
                exc_info=True,
            )
            _dem_xarr = None
        except Exception:
            logger.exception("the DEM could not be opened, retrying on the next request")
            return None
    return _dem_xarr


def _get_elevation(lon, lat):
    """Elevation in meters for a coordinate, or None if it cannot be read."""
    dem = _get_dem()
    if dem is None:
        return None
    try:
        return dem.sel(x=lon, y=lat, method="nearest").item()
    except Exception:
        logger.exception("the elevation could not be read for lon=%s lat=%s", lon, lat)
        return None


# -- AJAX popup --------------------------------------------------------------

def get_popup(request):
    fire_id = request.GET.get("id")
    if not fire_id:
        return JsonResponse({"error": "Missing id"}, status=400)

    try:
        fire_id = int(fire_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid id"}, status=400)

    active_fire = get_object_or_404(ActiveFire, id=fire_id)

    elevation = _get_elevation(active_fire.geom.x, active_fire.geom.y)

    popup_text = (
        '<span style="font-style: italic;display: block;text-align: center;">Foco de calor</span>'
        '<hr>'
        f'Fecha: {active_fire.date.strftime("%Y-%m-%d %H:%M")} HL<br/>'
        f'Lat: {round(active_fire.geom.y, 3)}&ensp;Lon: {round(active_fire.geom.x, 3)}<br/>'
        f'Fuente: {active_fire.source}<br/>'
        '<hr>'
        f'Radiación térmica: {active_fire.frp or "--"} MW<br/>'
        f'Temperatura: {int(round(active_fire.brightness - 273.15))} &#8451;<br/>'
        f'Confianza: {active_fire.confidence or "--"}<br/>'
        '<hr>'
        f'Elevación: {elevation if elevation is not None else "--"} msnm<br/>'
    )
    return JsonResponse(popup_text, safe=False)


# -- CSV download ------------------------------------------------------------

def _format_decimal(value):
    """Format a numeric value with comma as decimal separator, or empty string if None."""
    if value is None:
        return ''
    return str(value).replace(".", ",")


class _Echo:
    """Pseudo-buffer that returns written values directly (for streaming CSV)."""
    def write(self, value):
        return value


def download_result(request):
    url_referer = request.META.get('HTTP_REFERER')
    if not url_referer:
        return HttpResponse(status=204)

    query_params = parse_qs(urlparse(url_referer).query)
    from_date = query_params.get('from_date', [None])[0]
    to_date = query_params.get('to_date', [None])[0]
    region_slug = query_params.get('region', [None])[0]

    if not all([from_date, to_date, region_slug]):
        return HttpResponse(status=204)

    try:
        active_fires = _filter_active_fires(from_date, to_date, region_slug)
    except Region.DoesNotExist:
        return HttpResponse(status=204)

    header = [
        'Fecha (UTC-5)', 'Lat', 'Lon', 'Fuente',
        'Temperatura (C)', 'Temperatura Alt* (C)',
        'Radiación térmica (MW)', 'Confianza', 'Captura (Dia-Noche)',
        'Scan - real pixel size (km)', 'Track - real pixel size (km)',
    ]

    def generate_rows():
        yield header
        for af in active_fires.iterator():
            yield [
                af.date.strftime("%Y-%m-%d %H:%M"),
                _format_decimal(af.geom.y),
                _format_decimal(af.geom.x),
                af.source,
                _format_decimal(round(af.brightness - 273.15, 1) if af.brightness is not None else None),
                _format_decimal(round(af.brightness_alt - 273.15, 1) if af.brightness_alt is not None else None),
                _format_decimal(af.frp),
                af.confidence or '',
                af.day_night or '',
                _format_decimal(af.scan),
                _format_decimal(af.track),
            ]

    writer = csv.writer(_Echo(), delimiter=";")
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in generate_rows()),
        content_type="text/csv",
    )
    response['Content-Disposition'] = f'attachment; filename="{region_slug}_{from_date}_{to_date}.csv"'
    return response


# -- Home view ---------------------------------------------------------------

DEFAULT_EXTENT = "(16.130262012034756_-94.39453125_-6.970049417296218_-51.37207031249999)"


def home(request):
    required_params = ('from_date', 'to_date', 'extent', 'region')
    if not all(p in request.GET for p in required_params):
        return _redirect_with_defaults(request)

    extent_str = request.GET['extent']
    coords = [float(x) for x in extent_str.strip('()').split('_')]
    extent = [[coords[0], coords[1]], [coords[2], coords[3]]]

    last_active_fire = ActiveFire.objects.order_by('date').last()

    ba_first = BurnedArea.objects.order_by('date').first()
    ba_last = BurnedArea.objects.order_by('date').last()
    range_burned_area = ""
    years_burned_area = []
    if ba_first and ba_last:
        range_burned_area = f"de {ba_first.date.strftime('%Y-%m')} hasta {ba_last.date.strftime('%Y-%m')}"
        years_burned_area = list(
            BurnedArea.objects.values_list('date__year', flat=True)
            .distinct().order_by('date__year')
        )

    context = {
        "extent": extent,
        "af_last_update": last_active_fire.date if last_active_fire else None,
        "range_burned_area": range_burned_area,
        "years_burned_area": years_burned_area,
        "departments": Region.objects.filter(group=Region.Group.DEPARTAMENTOS),
        "natural_regions": Region.objects.filter(group=Region.Group.REGIONES_NATURALES),
        "parques_nacionales": Region.objects.filter(group=Region.Group.PARQUES_NACIONALES),
        "corporaciones": Region.objects.filter(group=Region.Group.CORPORACIONES),
        "burned_areas": BurnedArea.objects.all(),
    }

    return render(request, 'home.html', context)


def _redirect_with_defaults(request):
    """Redirect to home with default query parameters for missing values."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    params = {
        'from_date': request.GET.get('from_date', yesterday),
        'to_date': request.GET.get('to_date', date.today().isoformat()),
        'region': request.GET.get('region', 'colombia'),
        'extent': request.GET.get('extent', DEFAULT_EXTENT),
    }
    return redirect(f"/?{urlencode(params)}")
