from datetime import datetime, date
from page.models import ActiveFire


### Delete all entries of VIIRS Collection 1 for 2020

from_datetime = datetime.strptime("2020-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
to_datetime = datetime.strptime("2020-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")

active_fires = ActiveFire.objects.filter(source='VIIRS', date__gte=from_datetime, date__lte=to_datetime)

active_fires.delete()