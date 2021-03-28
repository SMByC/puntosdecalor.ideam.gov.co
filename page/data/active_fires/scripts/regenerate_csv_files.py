from datetime import datetime, date
from page.models import ActiveFire

from page.data.active_fires.import_active_fires import save_in_csv_table

### Regenerate all CSV files
#
# to run:
# python3.9 manage.py shell < page/data/active_fires/scripts/regenerate_csv_files.py

for item in ActiveFire.objects.all().order_by('date', 'source'):
    save_in_csv_table(item)

# specific for date  WARNING: comment for run as script

from_datetime = datetime.strptime("2020-10-04 00:00:00", "%Y-%m-%d %H:%M:%S")
to_datetime = datetime.strptime("2020-10-04 23:59:59", "%Y-%m-%d %H:%M:%S")

for item in ActiveFire.objects.filter(date__gte=from_datetime, date__lte=to_datetime).order_by('date', 'source'):
    save_in_csv_table(item)
