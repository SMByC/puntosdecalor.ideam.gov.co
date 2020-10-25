from datetime import datetime, date
from page.models import BurnedArea


### Delete specific entries

from_datetime = datetime.strptime("2020-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
to_datetime = datetime.strptime("2020-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")

burned_area = BurnedArea.objects.filter(date__gte=from_datetime, date__lte=to_datetime)

burned_area.delete()