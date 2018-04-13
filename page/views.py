#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

import json
from datetime import datetime, date
from urllib.parse import urlencode
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from djgeojson.views import GeoJSONLayerView

from page.models import ActiveFire, Region


class ActiveFiresMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        """Inspired by Glen Roberton's django-geojson-tiles view
        """
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')

        from_datetime = datetime.strptime(from_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        to_datetime = datetime.strptime(to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")

        qs = self.model.objects.filter(date__gte=from_datetime, date__lte=to_datetime)
        return qs


#### Ajax and json queries

def get_popup(request):
    id = int(request.GET["id"])
    active_fire = ActiveFire.objects.get(id=id)
    popup_text = \
        '<span style="font-style: italic;display: block;text-align: center;">Foco de calor</span>' \
        '<hr>' \
        'Fecha: {datetime} HLC<br/>' \
        'Lon: {lon}&ensp;Lat: {lat}<br/>' \
        'Satélite: {source}<br/>' \
        '<hr>' \
        'Temp. brillo: {brightness} C<br/>' \
        'Confianza: {confidence} %<br/>' \
        'Radiación térmica: {frp} MW<br/>' \
        .format(
            datetime=active_fire.date.strftime("%Y-%m-%d %H:%M"),
            lon=round(active_fire.geom.x, 3),
            lat=round(active_fire.geom.y, 3),
            source=active_fire.source,
            brightness=round(active_fire.brightness - 273.15, 2),
            confidence='--' if active_fire.confidence is None else active_fire.confidence,
            frp='--' if active_fire.frp is None else active_fire.frp,
        )
    return HttpResponse(json.dumps(popup_text))


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
    from_date = date.today() + relativedelta(days=-1)
    to_date = date.today()

    # set extent for Colombia
    extent = "(16.130262012034756_-94.39453125_-6.970049417296218_-51.37207031249999)"

    return response_with_get_parameters('/', {'from_date': from_date.isoformat(),
                                              'to_date': to_date.isoformat(),
                                              'extent': extent})


def home(request):
    # capturing the date range of period
    if 'from_date' in request.GET and 'to_date' in request.GET and 'extent'in request.GET:
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

    # get groups of regions
    departments = Region.objects.filter(group="departamentos").order_by('name')
    natural_regions = Region.objects.filter(group="regiones_naturales").order_by('name')

    context = {
        "extent": extent,
        "last_update": last_active_fire.date,
        "departments": departments,
        "natural_regions": natural_regions,
    }

    return render(request, 'home.html', context)
