#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2018
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

from django import forms

# data range picker
# https://github.com/longbill/jquery-date-range-picker


class Parameters(forms.Form):
    date_range = forms.CharField(label='')
    extent = forms.CharField(label='')
