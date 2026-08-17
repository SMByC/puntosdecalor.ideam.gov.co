# Local development of the Active Fires page (IDEAM - SMByC)
#
# Runs the whole site on SQLite/SpatiaLite with demo data, so no PostGIS
# server and no copy of the production database are needed.
#
#   make dev      environment + database + demo data + server  (start here)
#   make help     all the available targets
#
# Requirements: uv (https://docs.astral.sh/uv/) and the GEOS/GDAL/SpatiaLite
# system libraries -- `make doctor` tells you what is missing.

VENV        ?= .venv
PYTHON      := $(VENV)/bin/python
PORT        ?= 8005
HOST        ?= 127.0.0.1
DB          ?= local_dev.sqlite3
FIRES       ?= 4000

export DJANGO_SETTINGS_MODULE := active_fires.settings_local
export LOCAL_DB_PATH          := $(DB)

.DEFAULT_GOAL := help
.PHONY: help setup doctor db seed run dev check test check-responsive shell admin reset clean

help: ## show this help
	@echo "Active Fires - local development"
	@echo
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Variables: PORT=$(PORT) DB=$(DB) VENV=$(VENV) FIRES=$(FIRES)"

# -- environment -------------------------------------------------------------

$(PYTHON):
	@command -v uv >/dev/null || { \
		echo "uv is not installed: https://docs.astral.sh/uv/getting-started/installation/"; \
		exit 1; }
	uv venv $(VENV)
	uv pip install --python $(PYTHON) -r requirements-local.txt

setup: $(PYTHON) ## create the virtualenv with uv and install the local dependencies

doctor: $(PYTHON) ## check that GEOS, GDAL and SpatiaLite are available
	@$(PYTHON) dev/preflight.py

# -- database ----------------------------------------------------------------

$(DB): $(PYTHON)
	@$(PYTHON) dev/preflight.py
	$(PYTHON) manage.py migrate --run-syncdb --noinput
	$(PYTHON) manage.py seed_demo_data --fires $(FIRES)

db: $(DB) ## create the SpatiaLite database and fill it with demo data

seed: $(DB) ## regenerate the demo data (regions, hotspots, burned areas)
	$(PYTHON) manage.py seed_demo_data --fires $(FIRES)

reset: ## delete the local database and build it again from scratch
	rm -f $(DB)
	@$(MAKE) --no-print-directory db

# -- running -----------------------------------------------------------------

run: db ## run the development server (http://127.0.0.1:8000)
	@printf '\n  Active Fires -> http://$(HOST):$(PORT)/\n\n'
	$(PYTHON) manage.py runserver $(HOST):$(PORT) --nostatic

dev: run ## the usual entry point: environment + database + demo data + server

shell: db ## open a django shell against the local database
	$(PYTHON) manage.py shell

admin: db ## create a superuser for /admin/
	$(PYTHON) manage.py createsuperuser

# -- checks ------------------------------------------------------------------

check: $(PYTHON) ## run the django system checks
	$(PYTHON) manage.py check

test: db ## run the django test suite against the local database
	$(PYTHON) manage.py test

check-responsive: db ## headless check of the responsive layout (needs firefox)
	$(PYTHON) dev/responsive_check.py --port $(PORT)

# -- cleaning ----------------------------------------------------------------

clean: ## remove the virtualenv, the local database and the python caches
	rm -rf $(VENV) $(DB)
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
