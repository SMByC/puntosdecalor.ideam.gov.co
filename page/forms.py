from django import forms

# data range picker
# https://github.com/longbill/jquery-date-range-picker


class Period(forms.Form):
    date_range = forms.CharField(label='')
