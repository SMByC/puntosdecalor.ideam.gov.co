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
    <meta name="theme-color" content="#CC3D36">
    {# the listings hold the public downloadable data, they are meant to be found #}
    <meta name="robots" content="index, follow">
    <title>{% blocktranslate %}Index of {{ directory }}{% endblocktranslate %}</title>
    <style>
        :root {
            --brand: #CC3D36;
            --brand-soft: rgba(204, 61, 54, .10);
            --bg: #fafafa;
            --surface: #fff;
            --border: #e6e8ec;
            --text: #444;
            --text-2: #666;
            --text-3: #6e6e6e;
        }
        *, *::before, *::after { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 20px 16px 40px;
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 15px;
            line-height: 1.5;
            color: var(--text);
            background-color: var(--bg);
            overflow-wrap: anywhere;
        }
        .wrap { max-width: 900px; margin: 0 auto; }
        .back {
            display: inline-block;
            margin-bottom: 14px;
            padding: 6px 12px;
            font-size: .85rem;
            font-weight: 700;
            color: var(--brand);
            text-decoration: none;
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 999px;
        }
        .back:hover { color: #fff; background-color: var(--brand); border-color: var(--brand); }
        h1 { margin: 0 0 4px; font-size: 1.25rem; line-height: 1.3; color: var(--brand); }
        .dir { margin: 0 0 16px; font-size: .85rem; font-style: italic; color: var(--text-3); }
        .info {
            margin: 0 0 20px;
            padding: 4px 18px;
            font-size: .9rem;
            color: var(--text-2);
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-left: 4px solid var(--brand);
            border-radius: 8px;
        }
        .info a { color: var(--brand); }
        ul {
            margin: 0;
            padding: 0;
            list-style: none;
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }
        li + li { border-top: 1px solid var(--border); }
        li a {
            display: block;
            padding: 12px 16px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: .9rem;
            color: var(--brand);
            text-decoration: none;
        }
        li a:hover, li a:focus { background-color: var(--brand-soft); }
        li.up a { font-weight: 700; }
        @media (min-width: 700px) {
            body { padding: 32px 24px 48px; }
            h1 { font-size: 1.5rem; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <a class="back" href="/">&larr; Volver al mapa</a>

        <h1>{{ title }}</h1>
        <p class="dir">{{ directory }}</p>

        {% if info %}
        <div class="info">{{ info|safe }}</div>
        {% endif %}

        <ul>
        {% if directory != "/" %}
            <li class="up"><a href="../">../</a></li>
        {% endif %}
        {% for f in file_list %}
            <li><a href="{{ f|urlencode }}">{{ f }}</a></li>
        {% endfor %}
        </ul>
    </div>
</body>
</html>
"""
template_translatable = gettext_lazy("Index of %(directory)s")

HOTSPOT_INDEX_TITLE = (
    'Índice de archivos de puntos de calor por día para todo el territorio Colombiano'
)
HOTSPOT_INDEX_INFO = (
    '<p><strong>Formato:</strong> El formato CSV de los archivos usa "punto y coma" (;) como '
    'separador de elementos y usa "coma" (,) para la separación decimal. Las fechas están en '
    'hora local de Colombia (UTC-5)</p>'
    '<p><strong>Fuente:</strong> Detecciones de MODIS (1 km, satélites Aqua y Terra) y de VIIRS '
    '(375 m, satélites Suomi-NPP, NOAA-20 y NOAA-21) distribuidas por '
    '<a href="https://firms.modaps.eosdis.nasa.gov/">FIRMS</a> de la NASA, recortadas al '
    'territorio Colombiano</p>'
    '<p><strong>Acerca de:</strong> Si hace uso de estos datos realice la respectiva referencia '
    'a los datos originales de '
    '<a href="https://firms.modaps.eosdis.nasa.gov/active_fire/">MODIS y VIIRS</a>. '
    'Contacto referente a ésta página: xcorredorl@ideam.gov.co</p>'
)

BURNED_AREA_INDEX_TITLE = (
    'Índice de archivos de área quemada mensual para Colombia'
)
BURNED_AREA_INDEX_INFO = (
    '<p><strong>Formato:</strong> Archivos shapefile comprimidos en ZIP (EPSG:4326), un archivo '
    'por mes</p>'
    '<p><strong>Fuente:</strong> Producto '
    '<a href="https://lpdaac.usgs.gov/products/mcd64a1v061/">MODIS MCD64A1</a> (Colección 6.1), '
    'área quemada mensual de 500 m derivada de Terra y Aqua, '
    'procesado (disuelto y recortado) para el territorio Colombiano</p>'
    '<p><strong>Tenga en cuenta:</strong> cada píxel equivale a unas 25 hectáreas, por lo que las '
    'quemas pequeñas suelen subestimarse u omitirse, y el producto se publica algunos meses '
    'después del periodo observado. '
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
