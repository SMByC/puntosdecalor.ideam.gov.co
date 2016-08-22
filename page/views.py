from datetime import datetime, date
from urllib.parse import urlencode

from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from djgeojson.views import GeoJSONLayerView

from page.forms import Period
from page.models import ActiveFire


class ActiveFireMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        """Inspired by Glen Roberton's django-geojson-tiles view
        """
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')

        from_datetime = datetime.strptime(from_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        to_datetime = datetime.strptime(to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")

        qs = self.model.objects.filter(date__gte=from_datetime, date__lte=to_datetime)
        return qs


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

    return response_with_get_parameters('/', {'from_date': from_date.isoformat(),
                                              'to_date': to_date.isoformat()})


def home(request):
    # request from recalculate new period
    if 'date_range' in request.GET:
        date_range = request.GET.get('date_range')
        from_date = date_range.split(' - ')[0]
        to_date = date_range.split(' - ')[1]
        # redirect to a new URL:
        return response_with_get_parameters('/', {'from_date': from_date, 'to_date': to_date})

    # capturing the date range of period
    if 'from_date' in request.GET and 'to_date' in request.GET:
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

    # request without get parameters (url clean or first view)
    else:
        return init(request)

    form = Period(initial={'date_range': from_date + " - " + to_date})

    # get list of active fires inside period
    from_datetime = datetime.strptime(from_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    to_datetime = datetime.strptime(to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    qs_active_fires_in_period = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime).order_by('-date')

    # send the variables to process (variables that define the period, location, and more)
    get_parameters = urlencode({'from_date': from_date, 'to_date': to_date})

    context = {
        "form": form,
        "qs_active_fires_in_period": qs_active_fires_in_period,
        "get_parameters": get_parameters
    }

    return render(request, 'home.html', context)
