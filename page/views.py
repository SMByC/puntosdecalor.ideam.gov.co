import datetime

from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
from django.shortcuts import render
from djgeojson.views import GeoJSONLayerView

from page.forms import Period
from page.models import ActiveFire


class ActiveFireMapLayer(GeoJSONLayerView):
    def get_queryset(self):
        """
        Inspired by Glen Roberton's django-geojson-tiles view
        """

        from_datetime = datetime.datetime(int(self.kwargs['from_year']), int(self.kwargs['from_month']),
                                          int(self.kwargs['from_day']))
        to_datetime = datetime.datetime(int(self.kwargs['to_year']), int(self.kwargs['to_month']),
                                        int(self.kwargs['to_day']), hour=23, minute=59, second=59)

        # to_year = self.kwargs['to']

        qs = self.model.objects.filter(date__gte=from_datetime, date__lte=to_datetime)

        # print(self.di)

        return qs


def init(request):
    return home(request)


def home(request, from_year=None, from_month=None, from_day=None, to_year=None, to_month=None, to_day=None):
    # initialize the from_date (-1 days) and to_date (now)
    if from_year is None and from_month is None and from_day is None:
        date_now_1days = datetime.datetime.now() + relativedelta(days=-1)
        from_year = date_now_1days.year
        from_month = date_now_1days.month
        from_day = date_now_1days.day
    if to_year is None and to_month is None and to_day is None:
        date_now = datetime.datetime.now()
        to_year = date_now.year
        to_month = date_now.month
        to_day = date_now.day

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = Period(request.POST)
        # check whether it's valid:
        if form.is_valid():
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']

            # from_year=from_date.year
            # from_month=from_date.month from_day=None, to_year=None, to_month=None, to_day=None
            # print(from_year)
            # redirect to a new URL:
            return HttpResponseRedirect('/' + from_date.strftime("%Y-%m-%d") + '/' + to_date.strftime("%Y-%m-%d"))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = Period(
            initial={'from_date': datetime.date(int(from_year), int(from_month), int(from_day)),
                     'to_date': datetime.date(int(to_year), int(to_month), int(to_day))})

    # get list of active fires inside period
    from_datetime = datetime.datetime(int(from_year), int(from_month), int(from_day))
    to_datetime = datetime.datetime(int(to_year), int(to_month), int(to_day), hour=23, minute=59, second=59)
    qs_active_fires_in_period = ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime).order_by('-date')

    return render(request, 'home.html', locals())
