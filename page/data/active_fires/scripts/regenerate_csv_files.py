from datetime import datetime, date
from page.models import ActiveFire

from ..import_active_fires import save_in_csv_table

### Regenerate all CSV files

for item in ActiveFire.objects.all().order_by('date', 'source'):
    save_in_csv_table(item)

