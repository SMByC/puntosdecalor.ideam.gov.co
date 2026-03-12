#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Views for serving hotspot CSV files with an FTP-like directory listing.
"""

from pathlib import Path

from django.http import (
    Http404,
    FileResponse,
    HttpResponse,
    HttpResponseNotModified,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.template import Context, Template, loader
from django.template.exceptions import TemplateDoesNotExist
from django.utils.http import http_date, parse_http_date
from django.utils.translation import gettext as _, gettext_lazy


def serve(request, path, document_root=None, show_indexes=False,
          index_title='', index_info=''):
    """
    Serve static files below a given point in the directory structure.

    Provide ``document_root`` as a keyword argument. Set ``show_indexes``
    to ``True`` to render an FTP-like directory listing. Optional
    ``index_title`` and ``index_info`` customize the directory page.
    """
    document_root = Path(document_root)
    clean = _sanitize_path(path)

    if clean is None:
        raise Http404

    if clean != path:
        return HttpResponseRedirect(clean)

    fullpath = (document_root / clean).resolve()

    if not str(fullpath).startswith(str(document_root.resolve())):
        raise Http404

    if fullpath.is_dir():
        if show_indexes:
            return _directory_index(clean, fullpath, index_title, index_info)
        raise Http404(_("Directory indexes are not allowed here."))

    if not fullpath.exists():
        raise Http404(_('"%(path)s" does not exist') % {'path': fullpath})

    stat_result = fullpath.stat()
    if_modified = request.META.get('HTTP_IF_MODIFIED_SINCE')
    if if_modified and not _was_modified_since(if_modified, stat_result.st_mtime):
        return HttpResponseNotModified()

    response = FileResponse(fullpath.open('rb'))
    response["Last-Modified"] = http_date(stat_result.st_mtime)
    return response


def _sanitize_path(path):
    """Normalize a URL path and reject directory traversal attempts.

    Returns the cleaned path string, or None if the path is invalid.
    """
    from posixpath import normpath
    from urllib.parse import unquote

    path = normpath(unquote(path)).lstrip('/')
    parts = []
    for part in path.split('/'):
        if not part or part in ('.', '..'):
            continue
        parts.append(part)

    return '/'.join(parts) if parts else ''


# -- Directory listing -------------------------------------------------------

DEFAULT_DIRECTORY_INDEX_TEMPLATE = """\
{% load i18n %}
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="NONE,NOARCHIVE">
    <title>{% blocktranslate %}Index of {{ directory }}{% endblocktranslate %}</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; margin: 2em; color: #333; }
        h1 { font-size: 1.4em; }
        .info { background-color: #fffadd; padding: 1px 16px; margin: 8px 0; max-width: 800px; }
        ul { list-style: none; padding: 0; }
        li { padding: 2px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>

    {% if info %}
    <div class="info">{{ info|safe }}</div>
    {% endif %}

    <ul>
    {% if directory != "/" %}
        <li><a href="../">../</a></li>
    {% endif %}
    {% for f in file_list %}
        <li><a href="{{ f|urlencode }}">{{ f }}</a></li>
    {% endfor %}
    </ul>
</body>
</html>
"""
template_translatable = gettext_lazy("Index of %(directory)s")

HOTSPOT_INDEX_TITLE = (
    'Índice de archivos de puntos de calor por día para todo el territorio Colombiano'
)
HOTSPOT_INDEX_INFO = (
    '<p><strong>Formato:</strong> El formato CSV de los archivos usa "punto y coma" (;) como '
    'separador de elementos y usa "coma" (,) para la separación decimal</p>'
    '<p><strong>Acerca de:</strong> Si hace uso de estos datos realice la respectiva referencia '
    'a los datos originales de '
    '<a href="https://earthdata.nasa.gov/earth-observation-data/near-real-time/firms/c6-mcd14dl">MODIS</a> y '
    '<a href="https://earthdata.nasa.gov/earth-observation-data/near-real-time/firms/v1-vnp14imgt">VIIRS</a>. '
    'Contacto referente a ésta página: xcorredorl@ideam.gov.co</p>'
)

BURNED_AREA_INDEX_TITLE = (
    'Índice de archivos de área quemada mensual para Colombia'
)
BURNED_AREA_INDEX_INFO = (
    '<p><strong>Formato:</strong> Archivos shapefile comprimidos en ZIP (EPSG:4326)</p>'
    '<p><strong>Fuente:</strong> Producto '
    '<a href="https://modis-fire.umd.edu/ba.html">MODIS MCD64A1</a> '
    'procesado (disuelto y recortado) para el territorio Colombiano. '
    'Contacto: xcorredorl@ideam.gov.co</p>'
)


def _directory_index(path, fullpath, title='', info=''):
    """Render an FTP-like directory listing, files sorted newest first."""
    try:
        t = loader.select_template([
            'static/directory_index.html',
            'static/directory_index',
        ])
    except TemplateDoesNotExist:
        t = Template(DEFAULT_DIRECTORY_INDEX_TEMPLATE, name='Default directory index template')

    entries = []
    for entry in fullpath.iterdir():
        if entry.name.startswith('.'):
            continue
        name = f"{entry.name}/" if entry.is_dir() else entry.name
        entries.append(name)

    context = Context({
        'directory': path + '/' if path else '/',
        'file_list': sorted(entries, reverse=True),
        'title': title or _('Index of %(directory)s') % {'directory': path or '/'},
        'info': info,
    })
    return HttpResponse(t.render(context))


# -- Conditional request support ---------------------------------------------

def _was_modified_since(header, mtime):
    """Check if the resource was modified since the If-Modified-Since header value."""
    try:
        header_mtime = parse_http_date(header.split(';')[0])
        return int(mtime) > header_mtime
    except (ValueError, OverflowError):
        return True


def ftp_2_csv_redirect(request, path):
    return HttpResponsePermanentRedirect(f"/archivos-csv/{path}")
