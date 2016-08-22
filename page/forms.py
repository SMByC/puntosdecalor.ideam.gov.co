from django import forms

# data range picker
# https://github.com/longbill/jquery-date-range-picker


class Parameters(forms.Form):
    date_range = forms.CharField(label='')
    extent = forms.CharField(label='')
