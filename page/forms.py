from django import forms
from django.contrib.admin.widgets import AdminDateWidget

class Period(forms.Form):
    from_date = forms.DateField(required=True, widget = AdminDateWidget, label='Desde')
    to_date = forms.DateField(required=True, widget = AdminDateWidget, label='Hasta')
