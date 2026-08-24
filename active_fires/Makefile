# Production setup for puntosdecalor.ideam.gov.co (AlmaLinux 9)
#
# Installs / verifies the three deployment pieces that live in this
# directory and are NOT handled by update_Active_Fires.sh:
#
#   active_fires_nginx.conf  -> /etc/nginx/conf.d/  (rate limits, scanner 404s, www redirect)
#   nginx.tmpfiles.conf      -> /etc/tmpfiles.d/nginx.conf  (survives reboots, see header)
#   uwsgi.service            -> /etc/systemd/system/uwsgi.service
#   uwsgi.ini                (used in place, via WorkingDirectory)
#
# Plus: ensures /etc/nginx/nginx.conf has `user activefires;`
#
# Usage on the AlmaLinux 9 host — either from the repo root:
#   sudo make -C active_fires install
# or from inside this directory:
#   cd active_fires && sudo make install
# Source files are resolved from this Makefile's own location, so any other
# cwd works too (e.g. make -f .../Active_Fires/active_fires/Makefile check)
#
# All install targets are idempotent and print a diff before overwriting.
# See active_fires_nginx.conf and nginx.tmpfiles.conf headers for full rationale.

# resolve sources relative to this Makefile, independent of the invocation cwd
SELF_DIR        := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
SRC_NGINX_CONF  := $(SELF_DIR)/active_fires_nginx.conf
SRC_TMPFILES    := $(SELF_DIR)/nginx.tmpfiles.conf
SRC_UWSGI_SVC   := $(SELF_DIR)/uwsgi.service
SRC_UWSGI_INI   := $(SELF_DIR)/uwsgi.ini
TEST_CERTS_DIR  := $(SELF_DIR)/.nginx-test

DST_NGINX_CONF  := /etc/nginx/conf.d/active_fires_nginx.conf
DST_TMPFILES    := /etc/tmpfiles.d/nginx.conf
DST_UWSGI_SVC   := /etc/systemd/system/uwsgi.service

NGINX_MAIN_CONF := /etc/nginx/nginx.conf
SITE_URL        ?= https://puntosdecalor.ideam.gov.co
WWW_URL         := $(subst https://,https://www.,$(SITE_URL))

.DEFAULT_GOAL := help
.PHONY: help check check-nginx-main check-nginx check-tmpfiles check-uwsgi \
        install install-nginx install-tmpfiles install-uwsgi \
        verify verify-tmpfiles verify-nginx verify-uwsgi verify-reboot \
        diff status reload clean-tmp

help: ## show this help
	@echo "Active Fires — production setup (AlmaLinux 9)"
	@echo
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Run 'make check' before 'sudo make install'; then 'make verify'."

# -- preflight: compare repo vs installed without touching the system ---------

check: check-nginx-main check-nginx check-tmpfiles check-uwsgi ## preflight: diff repo vs installed, no writes

check-nginx-main: ## verify /etc/nginx/nginx.conf has user activefires
	@echo "== $(NGINX_MAIN_CONF) =="
	@if [ ! -f $(NGINX_MAIN_CONF) ]; then \
		echo "(skipped: $(NGINX_MAIN_CONF) not present — not a production host)"; \
	elif grep -qE '^\s*user\s+activefires\s*;' $(NGINX_MAIN_CONF); then \
		echo "ok  user activefires;"; \
	else \
		echo "FAIL user activefires not found in $(NGINX_MAIN_CONF)"; \
		echo "     fix: sudo sed -i 's/^\s*user.*/user activefires;/' $(NGINX_MAIN_CONF)"; exit 1; fi

check-nginx: ## diff nginx conf (repo vs /etc/nginx/conf.d/)
	@echo "== $(SRC_NGINX_CONF) -> $(DST_NGINX_CONF) =="
	@if [ ! -f $(DST_NGINX_CONF) ]; then echo "missing $(DST_NGINX_CONF) (will be created)"; \
	 else diff -u $(DST_NGINX_CONF) $(SRC_NGINX_CONF) --label installed --label repo || true; fi
	@echo
	@echo "syntax check (docker only: this file is an http-context snippet, not a"
	@echo "standalone config, and needs certs; the authoritative gate is the"
	@echo "'sudo nginx -t' inside install-nginx):"
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "  skipped (no docker on this host)"; \
	else \
		mkdir -p $(TEST_CERTS_DIR) && \
		openssl req -x509 -newkey rsa:2048 -keyout $(TEST_CERTS_DIR)/tls.key \
			-out $(TEST_CERTS_DIR)/tls.crt -days 2 -nodes -subj "/CN=check" 2>/dev/null; \
		docker run --rm \
			-v $(SRC_NGINX_CONF):/etc/nginx/conf.d/default.conf:ro \
			-v $(TEST_CERTS_DIR)/tls.crt:/etc/ssl/certs/wildcard_ideam_gov_co.crt:ro \
			-v $(TEST_CERTS_DIR)/tls.key:/etc/ssl/private/wildcard_ideam_gov_co.key:ro \
			nginx:alpine nginx -t 2>&1 | grep -E "syntax is ok|test is successful|\[emerg\]" | sed 's/^/  /'; \
		rm -rf $(TEST_CERTS_DIR); \
	fi

check-tmpfiles: ## diff tmpfiles (repo vs /etc/tmpfiles.d/ + vendor) and ownership
	@echo "== vendor /usr/lib/tmpfiles.d/nginx.conf =="
	@if [ -f /usr/lib/tmpfiles.d/nginx.conf ]; then cat /usr/lib/tmpfiles.d/nginx.conf; \
	 else echo "(not found — unexpected on EL9)"; fi
	@echo
	@echo "== $(SRC_TMPFILES) -> $(DST_TMPFILES) =="
	@if [ ! -f $(DST_TMPFILES) ]; then echo "missing $(DST_TMPFILES) (will be created)"; \
	 else diff -u $(DST_TMPFILES) $(SRC_TMPFILES) --label installed --label repo || true; fi
	@echo
	@echo "== ownership now =="
	@ls -ld /var/lib/nginx /var/lib/nginx/tmp 2>/dev/null || echo "/var/lib/nginx not present"
	@echo "expected after fix: drwxrwx--- activefires root ... /var/lib/nginx{,/tmp}"

check-uwsgi: ## diff uwsgi service + ini
	@echo "== $(SRC_UWSGI_SVC) -> $(DST_UWSGI_SVC) =="
	@if [ ! -f $(DST_UWSGI_SVC) ]; then echo "missing $(DST_UWSGI_SVC) (will be created)"; \
	 else diff -u $(DST_UWSGI_SVC) $(SRC_UWSGI_SVC) --label installed --label repo || true; fi
	@echo
	@echo "== $(SRC_UWSGI_INI) (used in place) =="
	@if [ -f $(SRC_UWSGI_INI) ]; then ls -l $(SRC_UWSGI_INI); else echo "missing $(SRC_UWSGI_INI)"; fi
	@systemctl is-active --quiet uwsgi 2>/dev/null && echo "uwsgi active" || echo "uwsgi not active (ok before install)"

diff: check ## alias for check
status: check ## alias for check

# -- install (requires sudo) -------------------------------------------------

install: install-nginx install-tmpfiles install-uwsgi ## install nginx + tmpfiles + uwsgi (all three)
	@echo
	@echo "All three pieces installed. Run 'make verify' and see header in $(SRC_NGINX_CONF)."

install-nginx: ## copy nginx conf -> /etc/nginx/conf.d/ + reload
	@echo "-> $(DST_NGINX_CONF)"
	@if [ ! -w $(dir $(DST_NGINX_CONF)) ] && [ "$$(id -u)" != "0" ]; then echo "need sudo: sudo make -C active_fires install-nginx"; exit 1; fi
	@if [ -f $(DST_NGINX_CONF) ]; then echo "diff before overwrite:"; diff -u $(DST_NGINX_CONF) $(SRC_NGINX_CONF) --label installed --label repo || true; fi
	sudo cp $(SRC_NGINX_CONF) $(DST_NGINX_CONF)
	sudo nginx -t
	sudo systemctl reload nginx
	@echo "ok  nginx reloaded"

install-tmpfiles: ## copy tmpfiles -> /etc/tmpfiles.d/ + apply
	@echo "-> $(DST_TMPFILES)  (replaces vendor /usr/lib/tmpfiles.d/nginx.conf)"
	@if [ ! -w $(dir $(DST_TMPFILES)) ] && [ "$$(id -u)" != "0" ]; then echo "need sudo: sudo make -C active_fires install-tmpfiles"; exit 1; fi
	@if [ -f $(DST_TMPFILES) ]; then echo "diff before overwrite:"; diff -u $(DST_TMPFILES) $(SRC_TMPFILES) --label installed --label repo || true; fi
	@echo "vendor file for reference:"
	@if [ -f /usr/lib/tmpfiles.d/nginx.conf ]; then cat /usr/lib/tmpfiles.d/nginx.conf | sed 's/^/  /'; \
	 else echo "  (no vendor file)"; fi
	sudo cp $(SRC_TMPFILES) $(DST_TMPFILES)
	sudo systemd-tmpfiles --create nginx.conf
	ls -ld /var/lib/nginx /var/lib/nginx/tmp
	@echo "ok  tmpfiles applied (ownership now activefires; will survive reboot)"

install-uwsgi: ## copy uwsgi.service -> /etc/systemd/system/ + daemon-reload + enable + restart
	@echo "-> $(DST_UWSGI_SVC)"
	@if [ ! -w $(dir $(DST_UWSGI_SVC)) ] && [ "$$(id -u)" != "0" ]; then echo "need sudo: sudo make -C active_fires install-uwsgi"; exit 1; fi
	@if [ -f $(DST_UWSGI_SVC) ]; then echo "diff before overwrite:"; diff -u $(DST_UWSGI_SVC) $(SRC_UWSGI_SVC) --label installed --label repo || true; fi
	sudo cp $(SRC_UWSGI_SVC) $(DST_UWSGI_SVC)
	sudo systemctl daemon-reload
	sudo systemctl enable uwsgi
	sudo systemctl restart uwsgi
	sudo systemctl status uwsgi --no-pager -l | head -n 25
	@echo "ok  uwsgi restarted (logs: journalctl -u uwsgi -f)"

# -- verify (mostly read-only) ------------------------------------------------

verify: verify-tmpfiles verify-nginx verify-uwsgi ## verify all three after install
	@echo
	@echo "Verify done. If verify-tmpfiles shows 13: Permission denied is gone and"
	@echo "verify-nginx shows 429 with Retry-After, the setup is correct."

verify-tmpfiles: ## ownership + large-response spill check
	@echo "== ownership =="
	ls -ld /var/lib/nginx /var/lib/nginx/tmp
	@if ls -ld /var/lib/nginx 2>/dev/null | grep -q activefires; then \
		echo "ok  /var/lib/nginx owned by activefires (survives reboot via /etc/tmpfiles.d)"; \
	else \
		echo "FAIL /var/lib/nginx not owned by activefires — run sudo make install-tmpfiles"; fi
	@echo
	@echo "== tmpfiles override present =="
	@if [ -f $(DST_TMPFILES) ]; then echo "ok  $(DST_TMPFILES) exists"; else echo "FAIL missing $(DST_TMPFILES)"; fi
	@if diff -q $(DST_TMPFILES) $(SRC_TMPFILES) >/dev/null 2>&1; then \
		echo "ok  $(DST_TMPFILES) matches repo"; \
	else \
		echo "WARN $(DST_TMPFILES) differs from repo — run make check"; fi
	@echo
	@echo "== spill test (large query, should not log 13:) =="
	@echo "   $(SITE_URL)/active_fires.json/?from_date=2025-01-01&to_date=2025-12-31&region=colombia"
	@curl -s "$(SITE_URL)/active_fires.json/?from_date=2025-01-01&to_date=2025-12-31&region=colombia" -o /dev/null -w "   http %{http_code} (%{size_download} bytes)\n" || echo "   (curl failed — check SITE_URL or network)"
	@echo "   permission errors in nginx error.log (CHECK TIMESTAMPS: lines older"
	@echo "   than the fix are historical and do not mean it failed):"
	@if [ -r /var/log/nginx/error.log ]; then \
		grep -i "open().*Permission denied" /var/log/nginx/error.log | tail -n 5 | sed 's/^/   /' \
			|| echo "   (none in the log at all — good)"; \
	else \
		echo "   (error.log not readable as $$(id -un) — rerun with sudo to inspect it)"; fi

verify-nginx: ## rate-limit 429 + Retry-After, scanner 404, bad UA 403, www redirect
	@echo "== nginx -t =="
	@sudo nginx -t 2>&1 | sed 's/^/  /'
	@if ! command -v curl >/dev/null 2>&1; then echo "curl not found — skipping HTTP checks"; exit 0; fi
	@echo
	@echo "== hammer heavy endpoint (expect some 429 with Retry-After) =="
	@echo "   (reliable when run ON the server; sequential curls over a WAN may"
	@echo "    stay under the burst bucket and report only 200s)"
	@for i in $$(seq 1 30); do \
		curl -s -o /dev/null -D - "$(SITE_URL)/active_fires.json/?from_date=2025-01-01&to_date=2025-01-02&region=colombia" \
		| tr -d '\r' | grep -iE "^HTTP/|^Retry-After:" | paste - - | head -n 1; \
	done | sort | uniq -c | sed 's/^/  /'
	@echo "   expected: mix of HTTP/1.1 200 and HTTP/1.1 429 with Retry-After: 10"
	@echo
	@echo "== scanner paths (expect 404, not proxied) =="
	@curl -s -o /dev/null -w "  /.env          -> %{http_code}\n" $(SITE_URL)/.env || true
	@curl -s -o /dev/null -w "  /wp-login.php  -> %{http_code}\n" $(SITE_URL)/wp-login.php || true
	@echo
	@echo "== bad UA (expect 403) =="
	@curl -s -A "sqlmap/1.5" -o /dev/null -w "  sqlmap UA -> %{http_code}\n" $(SITE_URL)/ || true
	@echo
	@echo "== www -> apex (expect 301) =="
	@curl -s -o /dev/null -w "  $(WWW_URL) -> %{http_code} -> %{redirect_url}\n" $(WWW_URL)/ || true

verify-uwsgi: ## uwsgi status, socket, recent logs
	@echo "== uwsgi =="
	@systemctl is-active --quiet uwsgi && echo "active" || echo "not active"
	@ls -l /var/run/uwsgi/uwsgi.sock 2>/dev/null || echo "socket missing /var/run/uwsgi/uwsgi.sock"
	@echo
	@journalctl -u uwsgi --no-pager -n 20 2>/dev/null | tail -n 20 || echo "(no journal)"

verify-reboot: ## checks to run immediately after a reboot (tmpfiles must stick)
	@echo "Post-reboot checks (tmpfiles must have survived):"
	ls -ld /var/lib/nginx /var/lib/nginx/tmp
	@systemctl is-active --quiet nginx && echo "nginx active" || echo "nginx NOT active"
	@systemctl is-active --quiet uwsgi && echo "uwsgi active" || echo "uwsgi NOT active"
	@echo
	@$(MAKE) --no-print-directory verify-tmpfiles

reload: ## reload nginx + uwsgi without copying configs
	sudo nginx -t && sudo systemctl reload nginx
	sudo systemctl restart uwsgi
	@echo "reloaded"

clean-tmp: ## remove stale uwsgi temp files (reloads nginx: workers recreate the hash tree)
	sudo rm -rf /var/lib/nginx/tmp/uwsgi/*
	sudo systemctl reload nginx
	@echo "ok  reloaded nginx — fresh workers recreated the uwsgi temp tree"
	ls -ld /var/lib/nginx/tmp/uwsgi
