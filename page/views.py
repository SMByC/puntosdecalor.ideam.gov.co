#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2020
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>
import csv
import json
from datetime import datetime, date
from urllib.parse import urlencode, urlparse, parse_qs
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from djgeojson.views import GeoJSONLayerView
from django.http import StreamingHttpResponse

from page.models import ActiveFire, Region, BurnedArea


class RegionMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        if self.request.method == 'GET' and 'region' in self.request.GET:
            region_slug = self.request.GET.get('region')
            qs = self.model.objects.filter(slug=region_slug)
            return qs


class BurnedAreaMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        if self.request.method == 'GET' and 'date' in self.request.GET:
            date_split = self.request.GET.get('date').split("-")
            ba_date = date(int(date_split[0]), int(date_split[1]), 1)
            qs = self.model.objects.get(date=ba_date)
            return qs


class ActiveFiresMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        """Inspired by Glen Roberton's django-geojson-tiles view
        """
        if self.request.method == 'GET' and 'from_date' in self.request.GET \
                and 'to_date' in self.request.GET and 'region' in self.request.GET:
            from_date = self.request.GET.get('from_date')
            to_date = self.request.GET.get('to_date')
            region_slug = self.request.GET.get('region')

            from_datetime = datetime.strptime(from_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
            to_datetime = datetime.strptime(to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")

            if region_slug == "colombia":
                active_fires = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime)
            else:
                region = Region.objects.get(slug=region_slug)
                active_fires = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime, geom__within=region.shape)
            return active_fires


#### Ajax and json queries

def get_popup(request):
    id = int(request.GET["id"])
    active_fire = ActiveFire.objects.get(id=id)
    popup_text = \
        '<span style="font-style: italic;display: block;text-align: center;">Foco de calor</span>' \
        '<hr>' \
        'Fecha: {datetime} HL<br/>' \
        'Lat: {lat}&ensp;Lon: {lon}<br/>' \
        'Fuente: {source}<br/>' \
        '<hr>' \
        'Radiación térmica: {frp} MW<br/>' \
        'Temperatura: {brightness} &#8451;<br/>' \
        'Confianza: {confidence}<br/>' \
        .format(
            datetime=active_fire.date.strftime("%Y-%m-%d %H:%M"),
            lon=round(active_fire.geom.x, 3),
            lat=round(active_fire.geom.y, 3),
            source=active_fire.source,
            brightness=int(round(active_fire.brightness - 273.15, 0)),
            confidence='--' if active_fire.confidence is None else active_fire.confidence,
            frp='--' if active_fire.frp is None else active_fire.frp,
        )
    return HttpResponse(json.dumps(popup_text))


class Echo:
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def download_result(request):
    # get the referer (previous) url with the query
    url_referer = request.META.get('HTTP_REFERER')
    query_params = parse_qs(urlparse(url_referer).query)
    if 'from_date' in query_params and 'to_date' in query_params and 'region' in query_params:
        from_date = query_params['from_date'][0]
        to_date = query_params['to_date'][0]
        region_slug = query_params['region'][0]
        # get data
        from_datetime = datetime.strptime(from_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        to_datetime = datetime.strptime(to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        try:
            if region_slug == "colombia":
                active_fires = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime)
            else:
                region = Region.objects.get(slug=region_slug)
                active_fires = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime,
                                                         geom__within=region.shape)
        except:
            return HttpResponse(status=204)
        # generate the data
        rows = [['Fecha (UTC-5)', 'Lat', 'Lon', 'Fuente', 'Temperatura (C)', 'Temperatura Alt* (C)',
                 'Radiación térmica (MW)', 'Confianza', 'Captura (Dia-Noche)',
                 'Scan - real pixel size (km)', 'Track - real pixel size (km)']]
        rows += [[active_fire.date.strftime("%Y-%m-%d %H:%M"), str(active_fire.geom.y).replace(".", ","),
                  str(active_fire.geom.x).replace(".", ","), active_fire.source,
                  '' if active_fire.brightness is None else str(round(active_fire.brightness - 273.15, 1)).replace(".", ","),
                  '' if active_fire.brightness_alt is None else str(round(active_fire.brightness_alt - 273.15, 1)).replace(".", ","),
                  '' if active_fire.frp is None else str(active_fire.frp).replace(".", ","),
                  '' if active_fire.confidence is None else active_fire.confidence,
                  '' if active_fire.day_night is None else active_fire.day_night,
                  '' if active_fire.scan is None else str(active_fire.scan).replace(".", ","),
                  '' if active_fire.track is None else str(active_fire.track).replace(".", ",")]
                 for active_fire in active_fires]

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer, delimiter=";")
        response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                         content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}_{}_{}.csv"'.format(region_slug, from_date, to_date)
        return response

    return HttpResponse(status=204)

#### Django response

def response_with_get_parameters(base_path, parameters):
    """Redirect to the url with get parameters"""
    # redirect to a new URL:
    response = redirect(base_path)
    response['Location'] += '?' + urlencode(parameters)
    return response


def init(request):
    """Set the default parameters from url clean or first view"""
    # initialize the from_date (-1 days) and to_date (now)
    from_date = request.GET.get('from_date') if 'from_date' in request.GET else (date.today() + relativedelta(days=-1)).isoformat()
    to_date = request.GET.get('to_date') if 'to_date' in request.GET else date.today().isoformat()
    region = request.GET.get('region') if 'region' in request.GET else "colombia"
    # saved map location
    extent = request.GET.get('extent') if 'extent' in request.GET else "(16.130262012034756_-94.39453125_-6.970049417296218_-51.37207031249999)"

    return response_with_get_parameters('/', {'from_date': from_date,
                                              'to_date': to_date,
                                              'extent': extent,
                                              'region': region})


def home(request):
    # capturing the date range of period
    if 'from_date' in request.GET and 'to_date' in request.GET and 'extent'in request.GET and 'region'in request.GET:
        # saved map location
        # extent -> [[lat-lng top-left], [lat-lng bottom-right]]
        extent = request.GET.get('extent')
        extent = [float(x) for x in extent.replace('(', '').replace(')', '').split('_')]
        extent = [[extent[0], extent[1]], [extent[2], extent[3]]]
    # request without get parameters (url clean or first view)
    else:
        return init(request)

    # get the last item
    last_active_fire = ActiveFire.objects.order_by('date').last()
    last_burned_area = BurnedArea.objects.order_by('date').last()

    # get groups of regions
    departments = Region.objects.filter(group="departamentos").order_by('name')
    natural_regions = Region.objects.filter(group="regiones_naturales").order_by('name')

    # get burned areas
    burned_areas = BurnedArea.objects.all().order_by('-date')

    context = {
        "extent": extent,
        "af_last_update": last_active_fire.date,
        "ba_last_update": last_burned_area.slug,
        "departments": departments,
        "natural_regions": natural_regions,
        "burned_areas": burned_areas,
    }

    return render(request, 'home.html', context)
