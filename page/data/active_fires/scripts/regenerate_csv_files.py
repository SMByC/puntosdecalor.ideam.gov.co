from datetime import datetime, date
from page.models import ActiveFire

from page.data.active_fires.import_active_fires import save_in_csv_table

### Regenerate all CSV files
#
# to run:
# python3.8 manage.py shell < page/data/active_fires/scripts/regenerate_csv_files.py

for item in ActiveFire.objects.all().order_by('date', 'source'):
    save_in_csv_table(item)

