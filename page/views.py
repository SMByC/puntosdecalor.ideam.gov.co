import datetime
import urllib

from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from djgeojson.views import GeoJSONLayerView

from page.forms import Period
from page.models import ActiveFire


class ActiveFireMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        """Inspired by Glen Roberton's django-geojson-tiles view
        """
        from_datetime = datetime.datetime(int(self.kwargs['from_year']), int(self.kwargs['from_month']),
                                          int(self.kwargs['from_day']))
        to_datetime = datetime.datetime(int(self.kwargs['to_year']), int(self.kwargs['to_month']),
                                        int(self.kwargs['to_day']), hour=23, minute=59, second=59)

        qs = self.model.objects.filter(date__gte=from_datetime, date__lte=to_datetime)
        return qs


def response_with_get_parameters(base_path, parameters):
    """Redirect to the url with get parameters"""
    # redirect to a new URL:
    response = redirect(base_path)
    response['Location'] += '?' + urllib.parse.urlencode(parameters)
    return response


def init(request):
    # initialize the from_date (-1 days) and to_date (now)
    from_date = datetime.date.today() + relativedelta(days=-1)
    to_date = datetime.date.today()

    return response_with_get_parameters('/', {'from_date': from_date.isoformat(),
                                              'to_date': to_date.isoformat()})


def home(request, from_year=None, from_month=None, from_day=None, to_year=None, to_month=None, to_day=None):

    if 'date_range' in request.GET:
        # create a form instance and populate it with data from the request:
        form = Period(request.GET)

        date_range = request.GET.get('date_range')
        from_date = date_range.split(' - ')[0]
        to_date = date_range.split(' - ')[1]

        # redirect to a new URL:
        return response_with_get_parameters('/', {'from_date': from_date, 'to_date': to_date})

    if 'from_date' in request.GET and 'to_date' in request.GET:
        from_date = request.GET.get('from_date').split('-')
        from_year = from_date[0]
        from_month = from_date[1]
        from_day = from_date[2]
        to_date = request.GET.get('to_date').split('-')
        to_year = to_date[0]
        to_month = to_date[1]
        to_day = to_date[2]
    else:
        return init(request)

    form = Period(
        initial={'date_range': "{}-{}-{}".format(from_year, from_month, from_day) + " - " +
                               "{}-{}-{}".format(to_year, to_month, to_day)})
    # get list of active fires inside period
    from_datetime = datetime.datetime(int(from_year), int(from_month), int(from_day))
    to_datetime = datetime.datetime(int(to_year), int(to_month), int(to_day), hour=23, minute=59, second=59)
    qs_active_fires_in_period = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime).order_by('-date')

    context = {
        "from_year": from_year,
        "from_month": from_month,
        "from_day": from_day,
        "to_year": to_year,
        "to_month": to_month,
        "to_day": to_day,
        "qs_active_fires_in_period": qs_active_fires_in_period,
        "form": form,
    }

    return render(request, 'home.html', context)
