#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Development-only views, wired in `active_fires/urls_local.py` and therefore
never reachable with the production settings.

The responsive check page loads the site in an iframe at a series of widths and
posts the measurements back, so `dev/responsive_check.py` can report them on
the console with a proper exit code.
"""

import json
from pathlib import Path

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

CHECK_PAGE = Path(__file__).resolve().parent / "responsive_check.html"

# last report posted by the browser (single process, development only)
_last_report = None


def responsive_check(request):
    """Serve the responsive check harness."""
    global _last_report
    _last_report = None
    return HttpResponse(CHECK_PAGE.read_text(encoding="utf-8"))


@csrf_exempt
def responsive_report(request):
    """Store (POST), hand over (GET) or drop (DELETE) the measurements of the
    last run. The runner drops them before starting so that a report left by a
    previous run is never mistaken for the current one."""
    global _last_report

    if request.method == "DELETE":
        _last_report = None
        return JsonResponse({"cleared": True})

    if request.method == "POST":
        try:
            _last_report = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as error:
            return JsonResponse({"error": f"invalid report: {error}"}, status=400)
        return JsonResponse({"stored": True})

    if _last_report is None:
        return JsonResponse({"pending": True}, status=404)
    return JsonResponse(_last_report)
