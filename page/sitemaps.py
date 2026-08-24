#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Sitemap of the stable entry points of the site: the map and the two public
data-file listings. The daily CSV files and monthly ZIPs are deliberately not
enumerated one by one: they churn constantly and the listing pages already
link them.
"""

from django.contrib.sitemaps import Sitemap


class StaticSitemap(Sitemap):
    protocol = 'https'

    def items(self):
        return [
            {'loc': '/', 'priority': 1.0, 'changefreq': 'daily'},
            {'loc': '/archivos-csv/', 'priority': 0.8, 'changefreq': 'daily'},
            {'loc': '/archivos-area-quemada/', 'priority': 0.8, 'changefreq': 'monthly'},
        ]

    def location(self, item):
        return item['loc']

    def priority(self, item):
        return item['priority']

    def changefreq(self, item):
        return item['changefreq']
