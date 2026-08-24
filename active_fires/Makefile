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

# Shell test reused by check and require-nginx-main: true when this is not a
# production host, or when nginx workers already run as activefires. The tmpfiles
# override chowns /var/lib/nginx to activefires, so applying it while workers
# still run as `nginx` would *cause* the 13: Permission denied it exists to fix.
NGINX_USER_OK = [ ! -f $(NGINX_MAIN_CONF) ] || grep -qE '^[[:space:]]*user[[:space:]]+activefires[[:space:]]*;' $(NGINX_MAIN_CONF)

# Written by any check-* target that finds a blocking problem and read by the
# summary in `check`. Named .log so the existing *.log rule in .gitignore covers
# it; check-reset clears it at the start of every preflight run.
CHECK_FLAG      := $(SELF_DIR)/.check-failed.log

# WorkingDirectory declared by the unit: uwsgi resolves `--ini uwsgi.ini` against
# it, so only the checkout living there is the one the running service reads.
# Both sides are compared canonicalised: abspath keeps whatever symlink the
# invocation used (`make -f /symlinked/path/Makefile` leaves it in SELF_DIR),
# and a deploy reached through a symlink is still the same checkout.
SELF_DIR_REAL   := $(realpath $(SELF_DIR))
UWSGI_WORKDIR    = $$(sed -n 's/^WorkingDirectory=//p' $(SRC_UWSGI_SVC) | tail -n 1)
UWSGI_WORKDIR_REAL = $$(readlink -f "$$wd" 2>/dev/null || echo "$$wd")

.DEFAULT_GOAL := help
# Prerequisite order carries meaning here: check-reset must clear the flag
# before any check-* appends to it, and install-nginx must land before
# install-tmpfiles chowns /var/lib/nginx. -j would reorder both.
.NOTPARALLEL:
.PHONY: help check check-reset check-nginx-main check-nginx check-tmpfiles \
        check-uwsgi require-nginx-main require-uwsgi-workdir \
        install install-nginx install-tmpfiles install-uwsgi \
        verify verify-tmpfiles verify-nginx verify-http verify-uwsgi verify-reboot \
        diff status reload clean-tmp clean-cache

help: ## show this help
	@echo "Active Fires — production setup (AlmaLinux 9)"
	@echo
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Run 'make check' before 'sudo make install'; then 'make verify'."

# -- preflight: compare repo vs installed without touching the system ---------

check: check-reset check-nginx-main check-nginx check-tmpfiles check-uwsgi ## preflight: diff repo vs installed, no writes
# Every check-* target reports and returns 0 so one FAIL cannot hide the other
# sections; each appends its blocking reasons to CHECK_FLAG and they are
# collected here, so a preflight can never end in "nothing blocks" while a
# section above it printed a FAIL.
	@echo
	@if [ -s $(CHECK_FLAG) ]; then \
		echo "PREFLIGHT FAILED — do not run 'sudo make install' yet:"; \
		sed 's/^/  /' $(CHECK_FLAG); rm -f $(CHECK_FLAG); exit 1; \
	else \
		rm -f $(CHECK_FLAG); \
		echo "preflight done — nothing blocks 'sudo make install'."; \
		echo "Any WARN above does not block, but it is what verify will report."; fi

check-reset:
	@rm -f $(CHECK_FLAG)

check-nginx-main: ## verify /etc/nginx/nginx.conf has user activefires
	@echo "== $(NGINX_MAIN_CONF) =="
	@if [ ! -f $(NGINX_MAIN_CONF) ]; then \
		echo "(skipped: $(NGINX_MAIN_CONF) not present — not a production host)"; \
	elif $(NGINX_USER_OK); then \
		echo "ok  user activefires;"; \
	else \
		echo "FAIL user activefires not found in $(NGINX_MAIN_CONF)"; \
		echo "     fix: sudo sed -i 's/^\s*user.*/user activefires;/' $(NGINX_MAIN_CONF)"; \
		echo "$(NGINX_MAIN_CONF) does not run workers as activefires: install-tmpfiles would chown /var/lib/nginx away from the uid nginx runs as" >> $(CHECK_FLAG); fi

# Hard gate for the install targets, kept separate from check-nginx-main so that
# a preflight run still reports every section instead of aborting on the first
# FAIL. install-tmpfiles must never run before this passes.
require-nginx-main:
	@if $(NGINX_USER_OK); then :; else \
		echo "FAIL $(NGINX_MAIN_CONF) does not have 'user activefires;'"; \
		echo "     The tmpfiles override chowns /var/lib/nginx{,/tmp} to activefires;"; \
		echo "     applying it while workers run as 'nginx' breaks every uwsgi and"; \
		echo "     client_body spill with 13: Permission denied."; \
		echo "     fix: sudo sed -i 's/^\s*user.*/user activefires;/' $(NGINX_MAIN_CONF)"; \
		echo "     then: sudo nginx -t && sudo systemctl restart nginx"; exit 1; fi

check-nginx: ## diff nginx conf (repo vs /etc/nginx/conf.d/)
	@echo "== $(SRC_NGINX_CONF) -> $(DST_NGINX_CONF) =="
	@if [ ! -f $(DST_NGINX_CONF) ]; then echo "missing $(DST_NGINX_CONF) (will be created)"; \
	 else diff -u $(DST_NGINX_CONF) $(SRC_NGINX_CONF) --label installed --label repo || true; fi
	@echo
	@echo "syntax check (docker only: this file is an http-context snippet, not a"
	@echo "standalone config, and needs certs; the authoritative gate is the"
	@echo "'sudo nginx -t' inside install-nginx, which rolls back on failure)."
	@echo "The container's full output is shown, warnings included. The"
	@echo "\"ssl_stapling ignored, no OCSP responder URL\" warning comes from the"
	@echo "throwaway self-signed cert generated here, not from the real one:"
# The config is copied into the (gitignored) test dir so the :z relabel needed on
# an SELinux-enforcing host lands on the copy, not on the tracked file. Every
# absolute path the config loads is stubbed with the throwaway cert, including
# the EL9 CA bundle: a missing ssl_trusted_certificate is an [emerg], and the
# container has no /etc/pki. docker's exit status is kept and split by [emerg],
# so a daemon-permission or image-pull error is never reported as a bad config
# and a genuinely bad config is never reported as a passing check.
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "  skipped (no docker on this host)"; \
	else \
		if ! { mkdir -p $(TEST_CERTS_DIR) && \
			cp $(SRC_NGINX_CONF) $(TEST_CERTS_DIR)/default.conf && \
			mkdir -p $(TEST_CERTS_DIR)/cache && \
			openssl req -x509 -newkey rsa:2048 -keyout $(TEST_CERTS_DIR)/tls.key \
				-out $(TEST_CERTS_DIR)/tls.crt -days 2 -nodes -subj "/CN=check" 2>/dev/null; }; then \
			echo "  WARN could not stage the test config/certs in $(TEST_CERTS_DIR)"; \
			echo "       the config was NOT validated here"; \
			rm -rf $(TEST_CERTS_DIR); \
		else \
		out=$$(docker run --rm \
			-v $(TEST_CERTS_DIR)/default.conf:/etc/nginx/conf.d/default.conf:ro,z \
			-v $(TEST_CERTS_DIR)/tls.crt:/etc/ssl/certs/wildcard_ideam_gov_co.crt:ro,z \
			-v $(TEST_CERTS_DIR)/tls.key:/etc/ssl/private/wildcard_ideam_gov_co.key:ro,z \
			-v $(TEST_CERTS_DIR)/tls.crt:/etc/pki/tls/certs/ca-bundle.crt:ro,z \
			-v $(TEST_CERTS_DIR)/cache:/var/lib/nginx/cache:z \
			nginx:alpine nginx -t 2>&1); rc=$$?; \
		rm -rf $(TEST_CERTS_DIR); \
		printf '%s\n' "$$out" | sed 's/^/  /'; \
		if [ $$rc -ne 0 ]; then \
			if printf '%s\n' "$$out" | grep -q '\[emerg\]'; then \
				echo "  FAIL nginx rejected this config — see the [emerg] line above"; \
				echo "$(SRC_NGINX_CONF) is rejected by nginx -t (see the [emerg] above)" >> $(CHECK_FLAG); \
			else \
				echo "  WARN docker nginx -t exited $$rc with no [emerg] — most likely a"; \
				echo "       daemon-permission or image-pull problem, not this config;"; \
				echo "       the config was NOT validated, so nothing here vouches for it"; \
			fi; \
		fi; \
		fi; \
	fi

check-tmpfiles: ## diff tmpfiles (repo vs /etc/tmpfiles.d/ + vendor) and ownership
	@echo "== vendor /usr/lib/tmpfiles.d/nginx.conf =="
	@if [ -f /usr/lib/tmpfiles.d/nginx.conf ]; then cat /usr/lib/tmpfiles.d/nginx.conf; \
	 else echo "(not found — unexpected on EL9)"; fi
	@echo
	@echo "== vendor vs repo =="
	@echo "   (the override replaces the vendor file wholesale, so any entry the"
	@echo "    vendor gains after 'dnf update nginx' must be mirrored by hand;"
	@echo "    the user field is the one difference that is intentional)"
	@if [ ! -f /usr/lib/tmpfiles.d/nginx.conf ]; then \
		echo "   (no vendor file — nothing to compare)"; \
	else \
		v=$$(mktemp); r=$$(mktemp); d=$$(mktemp); \
		awk '!/^[[:space:]]*#/ && NF {print $$1, $$2, $$3, $$5}' /usr/lib/tmpfiles.d/nginx.conf | sort > $$v; \
		awk '!/^[[:space:]]*#/ && NF {print $$1, $$2, $$3, $$5}' $(SRC_TMPFILES) | sort > $$r; \
		if diff -u $$v $$r --label vendor --label repo > $$d 2>&1; then \
			echo "   ok  same type/path/mode/group on every entry"; \
		else \
			echo "   WARN vendor and repo disagree beyond the user field:"; \
			sed 's/^/     /' $$d; \
			echo "     -> mirror the new or changed entries into $(SRC_TMPFILES)"; \
		fi; \
		rm -f $$v $$r $$d; \
	fi
	@echo
	@echo "== $(SRC_TMPFILES) -> $(DST_TMPFILES) =="
	@if [ ! -f $(DST_TMPFILES) ]; then echo "missing $(DST_TMPFILES) (will be created)"; \
	 else diff -u $(DST_TMPFILES) $(SRC_TMPFILES) --label installed --label repo || true; fi
	@echo
	@echo "== ownership now =="
	@ls -ld /var/lib/nginx /var/lib/nginx/tmp /var/lib/nginx/cache 2>/dev/null || echo "/var/lib/nginx not present"
	@echo "expected after fix: drwxrwx--- activefires root ... /var/lib/nginx{,/tmp,/cache}"

check-uwsgi: ## diff uwsgi service + ini
	@echo "== $(SRC_UWSGI_SVC) -> $(DST_UWSGI_SVC) =="
	@if [ ! -f $(DST_UWSGI_SVC) ]; then echo "missing $(DST_UWSGI_SVC) (will be created)"; \
	 else diff -u $(DST_UWSGI_SVC) $(SRC_UWSGI_SVC) --label installed --label repo || true; fi
	@echo
	@echo "== $(SRC_UWSGI_INI) (used in place) =="
	@if [ -f $(SRC_UWSGI_INI) ]; then ls -l $(SRC_UWSGI_INI); else echo "missing $(SRC_UWSGI_INI)"; fi
	@wd=$(UWSGI_WORKDIR); wdr=$(UWSGI_WORKDIR_REAL); \
	if [ "$$wdr" = "$(SELF_DIR_REAL)" ]; then \
		echo "ok  this checkout is the one uwsgi runs from"; \
	else \
		echo "WARN uwsgi.service sets WorkingDirectory=$$wd, this checkout is $(SELF_DIR_REAL)"; \
		echo "     the running service never reads the uwsgi.ini listed above"; fi
	@systemctl is-active --quiet uwsgi 2>/dev/null && echo "uwsgi active" || echo "uwsgi not active (ok before install)"

diff: check ## alias for check
status: check ## alias for check

# -- install (requires sudo) -------------------------------------------------

install: require-nginx-main install-nginx install-tmpfiles install-uwsgi ## install nginx + tmpfiles + uwsgi (all three)
	@echo
	@echo "All three pieces installed. Run 'make verify' and see header in $(SRC_NGINX_CONF)."

install-nginx: ## copy nginx conf -> /etc/nginx/conf.d/, validate (rollback on failure), reload
	@if [ "$$(id -u)" != "0" ]; then \
		echo "install needs root. rerun:"; \
		echo "  sudo make -C $(SELF_DIR) install-nginx"; exit 1; fi
	@echo "-> $(DST_NGINX_CONF)"
	@if [ -f $(DST_NGINX_CONF) ]; then echo "diff before overwrite:"; diff -u $(DST_NGINX_CONF) $(SRC_NGINX_CONF) --label installed --label repo || true; fi
# nginx -t reads the whole /etc/nginx tree, so the new file must be in place to
# be tested — which means a rejected file would otherwise stay installed and
# break the next reboot or `dnf update nginx` long after this run. Keep a copy
# and restore it on failure. The .bak suffix stays out of `include conf.d/*.conf`.
	@if [ -f $(DST_NGINX_CONF) ]; then cp -p $(DST_NGINX_CONF) $(DST_NGINX_CONF).bak; fi
	cp $(SRC_NGINX_CONF) $(DST_NGINX_CONF)
	@if nginx -t; then \
		rm -f $(DST_NGINX_CONF).bak; \
	else \
		echo "FAIL nginx -t rejected the new config — rolling back"; \
		if [ -f $(DST_NGINX_CONF).bak ]; then mv $(DST_NGINX_CONF).bak $(DST_NGINX_CONF); \
		else rm -f $(DST_NGINX_CONF); fi; \
		if nginx -t >/dev/null 2>&1; then echo "ok  previous config restored, nginx -t passes again"; \
		else echo "WARN previous config restored but nginx -t still fails — unrelated problem"; fi; \
		exit 1; fi
	systemctl reload nginx
	@echo "ok  nginx reloaded"

install-tmpfiles: require-nginx-main ## copy tmpfiles -> /etc/tmpfiles.d/ + apply
	@if [ "$$(id -u)" != "0" ]; then \
		echo "install needs root. rerun:"; \
		echo "  sudo make -C $(SELF_DIR) install-tmpfiles"; exit 1; fi
	@echo "-> $(DST_TMPFILES)  (replaces vendor /usr/lib/tmpfiles.d/nginx.conf)"
	@if [ -f $(DST_TMPFILES) ]; then echo "diff before overwrite:"; diff -u $(DST_TMPFILES) $(SRC_TMPFILES) --label installed --label repo || true; fi
	@echo "vendor file for reference:"
	@if [ -f /usr/lib/tmpfiles.d/nginx.conf ]; then sed 's/^/  /' /usr/lib/tmpfiles.d/nginx.conf; \
	 else echo "  (no vendor file)"; fi
	cp $(SRC_TMPFILES) $(DST_TMPFILES)
	systemd-tmpfiles --create nginx.conf
	@ls -ld /var/lib/nginx /var/lib/nginx/tmp /var/lib/nginx/cache 2>/dev/null \
		|| echo "WARN /var/lib/nginx{,/tmp,/cache} still missing after systemd-tmpfiles --create"
	@echo "ok  tmpfiles applied (ownership now activefires; will survive reboot)"

install-uwsgi: require-uwsgi-workdir ## copy uwsgi.service -> /etc/systemd/system/ + daemon-reload + enable + restart
	@if [ "$$(id -u)" != "0" ]; then \
		echo "install needs root. rerun:"; \
		echo "  sudo make -C $(SELF_DIR) install-uwsgi"; exit 1; fi
	@echo "-> $(DST_UWSGI_SVC)"
	@if [ -f $(DST_UWSGI_SVC) ]; then echo "diff before overwrite:"; diff -u $(DST_UWSGI_SVC) $(SRC_UWSGI_SVC) --label installed --label repo || true; fi
	cp $(SRC_UWSGI_SVC) $(DST_UWSGI_SVC)
	systemctl daemon-reload
	systemctl enable uwsgi
	systemctl restart uwsgi
	systemctl status uwsgi --no-pager -l | head -n 25 || true
	@echo "ok  uwsgi restarted (logs: journalctl -u uwsgi -f)"

# Hard gate for install-uwsgi: the unit pins WorkingDirectory and resolves
# `--ini uwsgi.ini` against it, so installing from a different checkout restarts
# a service that keeps reading someone else's uwsgi.ini — every process-model or
# harakiri edit made here would be invisible while check-uwsgi still lists it.
require-uwsgi-workdir:
	@wd=$(UWSGI_WORKDIR); wdr=$(UWSGI_WORKDIR_REAL); \
	if [ "$$wdr" = "$(SELF_DIR_REAL)" ]; then :; else \
		echo "FAIL this checkout is $(SELF_DIR_REAL)"; \
		echo "     but $(SRC_UWSGI_SVC) sets WorkingDirectory=$$wd"; \
		echo "     uwsgi resolves --ini uwsgi.ini there, so restarting it from here"; \
		echo "     would reload $$wd/uwsgi.ini and ignore every edit made in this tree."; \
		echo; \
		echo "     Either run make from $$wd, or move the deploy to this checkout —"; \
		echo "     the path is pinned in more than this unit:"; \
		echo "       uwsgi.service            WorkingDirectory, ExecStart, EnvironmentFile"; \
		echo "       uwsgi.ini                set-placeholder base"; \
		echo "       active_fires_nginx.conf  alias for /static/"; \
		echo "       update_Active_Fires.sh   PROJECT_DIR"; \
		echo "       page/data/*/crontab.crt  APP_DIR and ENV_FILE"; exit 1; fi

# -- verify (mostly read-only) ------------------------------------------------

verify: verify-tmpfiles verify-nginx verify-uwsgi ## verify all three after install
	@echo
	@echo "Verify done. If verify-tmpfiles shows 13: Permission denied is gone and"
	@echo "verify-nginx shows 429 with Retry-After, the setup is correct."

verify-tmpfiles: ## ownership + large-response spill check
	@echo "== ownership =="
	@ls -ld /var/lib/nginx /var/lib/nginx/tmp /var/lib/nginx/cache 2>/dev/null || echo "(/var/lib/nginx and its subdirectories are not all present)"
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
	@if command -v curl >/dev/null 2>&1; then \
		curl -s --connect-timeout 10 -m 60 "$(SITE_URL)/active_fires.json/?from_date=2025-01-01&to_date=2025-12-31&region=colombia" -o /dev/null -w "   http %{http_code} (%{size_download} bytes)\n" \
			|| echo "   (curl failed — check SITE_URL or network)"; \
	else \
		echo "   (curl not found — skipping the spill request)"; fi
	@echo "   permission errors in nginx error.log (CHECK TIMESTAMPS: lines older"
	@echo "   than the fix are historical and do not mean it failed):"
# A pipeline reports the exit status of its last command, so `|| echo` after
# grep | tail | sed would never fire: the matches are captured and tested.
	@if [ -r /var/log/nginx/error.log ]; then \
		hits=$$(grep -i "open().*Permission denied" /var/log/nginx/error.log | tail -n 5); \
		if [ -n "$$hits" ]; then printf '%s\n' "$$hits" | sed 's/^/   /'; \
		else echo "   (none in the log at all — good)"; fi; \
	else \
		echo "   (error.log not readable as $$(id -un) — rerun with sudo to inspect it)"; fi

verify-nginx: ## nginx -t, then the HTTP checks (see verify-http)
	@echo "== nginx -t =="
	@if command -v nginx >/dev/null 2>&1 || [ -x /usr/sbin/nginx ]; then \
# The redirection runs as the invoking user, before sudo: writing into the
# checkout fails for any operator without write access there and would report a
# perfectly good config as "FAIL nginx -t". mktemp keeps it in the caller's tmp.
		log=$$(mktemp); \
		sudo nginx -t > $$log 2>&1; rc=$$?; \
		sed 's/^/  /' $$log; rm -f $$log; \
		if [ $$rc -ne 0 ]; then echo "  FAIL nginx -t"; exit $$rc; fi; \
	else \
		echo "  skipped (nginx not installed on this host)"; fi
# A bare `exit 0` would only end its own recipe line — make runs every line in a
# separate shell — so the curl guard has to choose whether to run the HTTP
# target at all instead of trying to skip the lines that follow.
	@if command -v curl >/dev/null 2>&1; then \
		$(MAKE) --no-print-directory verify-http; \
	else \
		echo; echo "curl not found — skipping HTTP checks"; fi

verify-http: ## rate-limit 429 + Retry-After, scanner 404, bad UA 403, www redirect (needs curl)
	@echo
	@echo "== hammer heavy endpoint (expect some 429 with Retry-After) =="
	@echo "   (reliable when run ON the server; sequential curls over a WAN may"
	@echo "    stay under the burst bucket and report only 200s)"
	@for i in $$(seq 1 30); do \
		curl -s --connect-timeout 10 -m 20 -o /dev/null -D - "$(SITE_URL)/active_fires.json/?from_date=2025-01-01&to_date=2025-01-02&region=colombia" \
		| tr -d '\r' | grep -iE "^HTTP/|^Retry-After:" | paste - - | head -n 1; \
	done | sort | uniq -c | sed 's/^/  /'
	@echo "   expected: mix of HTTP/1.1 200 and HTTP/1.1 429 with Retry-After: 10"
	@echo
	@echo "== scanner paths (expect 404, not proxied) =="
	@curl -s --connect-timeout 10 -m 15 -o /dev/null -w "  /.env          -> %{http_code}\n" $(SITE_URL)/.env || true
	@curl -s --connect-timeout 10 -m 15 -o /dev/null -w "  /wp-login.php  -> %{http_code}\n" $(SITE_URL)/wp-login.php || true
	@echo
	@echo "== bad UA (expect 403) =="
	@curl -s -A "sqlmap/1.5" -o /dev/null -w "  sqlmap UA -> %{http_code}\n" $(SITE_URL)/ || true
	@echo
	@echo "== www -> apex (expect 301) =="
	@curl -s --connect-timeout 10 -m 15 -o /dev/null -w "  $(WWW_URL) -> %{http_code} -> %{redirect_url}\n" $(WWW_URL)/ || true

verify-uwsgi: ## uwsgi status, socket, recent logs
	@echo "== uwsgi =="
	@systemctl is-active --quiet uwsgi && echo "active" || echo "not active"
	@ls -l /var/run/uwsgi/uwsgi.sock 2>/dev/null || echo "socket missing /var/run/uwsgi/uwsgi.sock"
	@echo
	@journalctl -u uwsgi --no-pager -n 20 2>/dev/null | tail -n 20 || echo "(no journal)"

verify-reboot: ## checks to run immediately after a reboot (tmpfiles must stick)
	@echo "Post-reboot checks (tmpfiles must have survived):"
	@ls -ld /var/lib/nginx /var/lib/nginx/tmp /var/lib/nginx/cache 2>/dev/null || echo "(/var/lib/nginx and its subdirectories are not all present)"
	@systemctl is-active --quiet nginx && echo "nginx active" || echo "nginx NOT active"
	@systemctl is-active --quiet uwsgi && echo "uwsgi active" || echo "uwsgi NOT active"
	@echo
	@$(MAKE) --no-print-directory verify-tmpfiles

reload: ## reload nginx + uwsgi without copying configs
	sudo nginx -t && sudo systemctl reload nginx
# Graceful on purpose: ExecReload sends SIGHUP to the uwsgi master, so workers
# finish in-flight requests (a multi-minute /download-result/ export) instead of
# being torn down. Same order as update_Active_Fires.sh; restart only as fallback.
	sudo systemctl reload uwsgi || sudo systemctl restart uwsgi
	@echo "reloaded"

clean-cache: ## drop the cached hotspot answers (use when you need fresh data NOW)
# The 60 s TTL in active_fires_nginx.conf means waiting is usually enough; this
# is for the moment an import has just landed and the answer has to change now.
# Same reason as clean-tmp for letting root expand the path: the directory is
# 0770 activefires:root and a maintenance user's shell cannot read it.
	@if sudo test -d /var/lib/nginx/cache; then \
		sudo find /var/lib/nginx/cache -mindepth 1 -delete; \
		echo "ok  emptied /var/lib/nginx/cache"; \
	else \
		echo "(/var/lib/nginx/cache not present — nothing to clean)"; fi
	sudo systemctl reload nginx
	@echo "ok  reloaded nginx — the next hotspot query goes straight to uWSGI"

clean-tmp: ## remove stale uwsgi temp files (reloads nginx: workers recreate the hash tree)
# The glob has to be expanded by root: /var/lib/nginx is 0770 activefires:root,
# so a maintenance user's own shell cannot read it and the unexpanded pattern
# makes `rm -rf` a silent no-op that still reports success.
	@if sudo test -d /var/lib/nginx/tmp/uwsgi; then \
		sudo find /var/lib/nginx/tmp/uwsgi -mindepth 1 -delete; \
		echo "ok  emptied /var/lib/nginx/tmp/uwsgi"; \
	else \
		echo "(/var/lib/nginx/tmp/uwsgi not present — nothing to clean)"; fi
	sudo systemctl reload nginx
	@echo "ok  reloaded nginx — fresh workers recreated the uwsgi temp tree"
	@sudo ls -ld /var/lib/nginx/tmp/uwsgi 2>/dev/null || echo "(recreated on the first spill)"
