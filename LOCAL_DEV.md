# Running the page locally

The production site runs on PostGIS. To open and test the page on a laptop
there is a parallel, self-contained setup: **SQLite/SpatiaLite + demo data +
`uv`**, driven by the `Makefile`. Nothing of the production configuration is
modified — the local run only adds `active_fires/settings_local.py`.

```bash
make dev
```

That single command creates the virtualenv, installs the dependencies, builds
the database, fills it with demo data and starts the server at
<http://127.0.0.1:8000>.

## Requirements

| Tool | Why | Install |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | virtualenv + dependencies | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| GEOS, GDAL | GeoDjango geometry support | `pacman -S geos gdal` · `apt install libgeos-c1v5 gdal-bin` |
| SpatiaLite | spatial SQLite (`mod_spatialite`) | `pacman -S libspatialite` · `apt install libsqlite3-mod-spatialite` |

`make doctor` reports exactly what is missing, with the install command for the
usual distributions. On macOS, point Django at Homebrew's library:

```bash
export SPATIALITE_LIBRARY_PATH=$(brew --prefix)/lib/mod_spatialite.dylib
```

## Targets

```
make help              list every target
make setup             create .venv with uv and install requirements-local.txt
make doctor            check GEOS, GDAL and SpatiaLite
make db                create the SpatiaLite database and load the demo data
make seed              regenerate the demo data
make reset             delete the database and build it again
make run               development server (http://127.0.0.1:8000)
make dev               setup + db + seed + run
make shell             django shell against the local database
make admin             create a superuser for /admin/
make check             django system checks
make test              django test suite
make check-responsive  headless check of the responsive layout
make clean             remove .venv, the database and the caches
```

Variables: `PORT=8010 make run`, `FIRES=15000 make seed`, `DB=/tmp/af.sqlite3`,
`VENV=/tmp/af-venv`.

## The demo data

`make db` runs `manage.py seed_demo_data`, which creates:

- **26 regions** — Colombia plus departments, natural regions, national parks
  and corporations, so the region drop-list, the zoom-to-region and the spatial
  filter all work;
- **4 000 hotspots** spread over the last 30 days, clustered around the usual
  burning areas (Caquetá/Meta arc, Guaviare, Vichada savannas);
- **24 monthly burned areas**, so the multi-select and the per-year shortcuts
  have something to draw;
- **a few CSV/ZIP files** under `page/data/ftp_files/` and
  `page/data/ftp_ba_files/`, so `/archivos-csv/` and `/archivos-area-quemada/`
  are not empty.

> The geometries are rough approximations (bounding boxes and a simplified
> country outline). They are for local testing only and the command refuses to
> run against a PostGIS database.

Options: `--fires N`, `--days N`, `--months N`, `--seed N`, `--keep`.

## Differences with production

| | production | local |
|---|---|---|
| database | PostGIS | SQLite + SpatiaLite (`local_dev.sqlite3`) |
| settings | `active_fires.settings` | `active_fires.settings_local` |
| `DEBUG` | `False` | `True` (static files served by `runserver`) |
| migrations | tables created by hand | `migrate --run-syncdb` from the models |
| elevation in the popups | read from `static/dem/DEM_COL.img` | shows `--`, the DEM is not in the repository |
| map tiles | from the tile providers | the same, so an internet connection is needed |

## Checking the responsive layout

```bash
make check-responsive
```

It loads the page in a headless browser (firefox, or chromium as a fallback) at
14 viewport widths from 320 px to 1920 px and checks that nothing overflows
horizontally, that the lateral panel switches between drawer and docked at the
900 px breakpoint, and that no javascript error is raised. It exits non-zero
when something breaks, so it can be used in a pre-commit hook or CI.

```
width  panel      map        h-scroll     overflowing
------------------------------------------------------------
  320px  drawer    320x648    no           0
  ...
  900px  docked    580x644    no           0
 1920px  docked   1560x844    no           0

OK: no horizontal overflow at any of the 14 widths, no javascript errors
```

The same page can be opened by hand at <http://127.0.0.1:8000/_dev/responsive/>
while `make run` is going, which is handy to watch the sweep. Those `_dev/`
URLs only exist with the local settings.

The check reuses a server that is already running on the port, and refuses to
run if the port belongs to some other program — in that case stop it or pick
another port, `make check-responsive PORT=8010`.
