from django import forms

# data range picker
# https://github.com/longbill/jquery-date-range-picker

class Period(forms.Form):
    from_date = forms.DateField(required=True, label='De', widget=forms.widgets.DateInput(format="%Y-%m-%d"))
    to_date = forms.DateField(required=True, label='a', widget=forms.widgets.DateInput(format="%Y-%m-%d"))
