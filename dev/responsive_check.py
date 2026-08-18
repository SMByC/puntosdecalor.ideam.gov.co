#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  (c) Copyright SMByC-IDEAM, 2016-2026
#  Authors: Xavier Corredor Ll. <xcorredorl@ideam.gov.co>

"""
Check the responsive layout of the page without a browser session.

Starts the development server, opens `/_dev/responsive/` in a headless browser
(which measures the page at a series of viewport widths) and prints the result:

    make check-responsive
    python dev/responsive_check.py --port 8010

Exit code 0 when no width overflows horizontally and no javascript error was
raised, 1 when something is wrong, 2 when the check could not be run.
"""

import argparse
import getpass
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FIREFOX = ["firefox", "firefox-esr"]
CHROMIUM = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable"]


def find_browser(preferred=None):
    """Return (path, kind) of the first headless-capable browser found."""
    names = [preferred] if preferred else FIREFOX + CHROMIUM
    for name in names:
        path = shutil.which(name)
        if path:
            kind = "firefox" if "firefox" in Path(path).name else "chromium"
            return path, kind
    return None, None


def profile_dir_for(kind):
    """Kept between runs (creating a fresh firefox profile every time is slow),
    but private to this user and never shared between browsers."""
    owner = getattr(os, "getuid", lambda: getpass.getuser())()
    return Path(tempfile.gettempdir()) / f"active-fires-{kind}-profile-{owner}"

FIREFOX_PREFS = """\
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("app.update.enabled", false);
user_pref("extensions.autoDisableScopes", 15);
user_pref("network.dns.disablePrefetch", true);
"""


def prepare_profile(kind):
    directory = profile_dir_for(kind)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if kind == "firefox":
        (directory / "user.js").write_text(FIREFOX_PREFS, encoding="utf-8")
    return str(directory)


def browser_command(path, kind, url, profile_dir):
    if kind == "firefox":
        return [path, "--headless", "--new-instance", "--profile", profile_dir, url]
    # no --dump-dom / --virtual-time-budget: both make chrome exit (or skew the
    # timers) before the harness has finished measuring and posted its report
    return [path, "--headless=new", "--disable-gpu", "--no-first-run",
            "--no-default-browser-check", f"--user-data-dir={profile_dir}", url]


def port_is_open(host, port):
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex((host, port)) == 0


def wait_for_port(host, port, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_is_open(host, port):
            return True
        time.sleep(0.25)
    return False


def start_server(host, port):
    """Start runserver, logging to a temporary file: runserver writes a line per
    request to stderr and a pipe nobody reads would eventually block it."""
    env = dict(os.environ, DJANGO_SETTINGS_MODULE="active_fires.settings_local")
    python = BASE_DIR / ".venv" / "bin" / "python"
    log = tempfile.NamedTemporaryFile(prefix="active-fires-runserver-", suffix=".log", delete=False)
    process = subprocess.Popen(
        [str(python if python.exists() else sys.executable), "manage.py", "runserver",
         f"{host}:{port}", "--noreload", "--skip-checks", "--nostatic"],
        cwd=str(BASE_DIR), env=env,
        stdout=log, stderr=subprocess.STDOUT,
    )
    process.log_path = log.name
    if not wait_for_port(host, port):
        process.terminate()
        print(f"the development server did not start on {host}:{port}\n"
              + Path(log.name).read_text(errors="ignore")[-2000:])
        return None
    return process


def clear_report(base_url):
    """Drop any report left behind by a previous run.

    Doubles as the identity check of the server: only this project's local
    settings answer DELETE on that endpoint, so a port taken by an unrelated
    service is detected before the browser is started.
    """
    request = urllib.request.Request(f"{base_url}/_dev/responsive/report/", method="DELETE")
    try:
        with urllib.request.urlopen(request, timeout=5) as answer:
            return json.loads(answer.read().decode("utf-8")).get("cleared") is True
    except Exception:
        return False


def poll_report(base_url, timeout=150):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/_dev/responsive/report/", timeout=5) as answer:
                return json.loads(answer.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code != 404:  # 404 just means "no report yet"
                print(f"unexpected answer from {base_url}/_dev/responsive/report/: "
                      f"HTTP {error.code} {error.reason}")
                return None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        except ValueError as error:  # includes JSONDecodeError
            print(f"unexpected answer from {base_url}/_dev/responsive/report/: {error}")
            return None
        time.sleep(0.5)
    return None


def print_report(report):
    """Print the measurements, return True when everything passed."""
    results = report.get("results", [])
    errors = report.get("errors", [])
    checks = report.get("checks", [])

    print(f"\n{'width':>7}  {'panel':<7} {'map':>11}  {'slider':<11} {'h-scroll':<12} overflowing")
    print("-" * 76)

    failed = []
    for step in results:
        overflow = step["horizontalScroll"]
        crossing = step["overflowing"]
        ok = not overflow and not crossing
        if not ok:
            failed.append(step)
        slider = (f"{step.get('sliderAt', '-')} {step.get('sliderWidth', 0)}px"
                  if step.get('slider') else "hidden")
        print(f"{step['width']:>5}px  {step['panel']:<7} "
              f"{step['mapWidth']:>5}x{step['mapHeight']:<5} "
              f"{slider:<11} "
              f"{('YES ' + str(overflow) + 'px') if overflow else 'no':<12} "
              f"{len(crossing)}{'' if ok else '  <-- ' + '; '.join(crossing[:3])}")

    reference = results[0] if results else {}
    painted = sum(1 for step in results if step.get('hotspotsPainted'))
    print(f"\nplugins: date picker {'ok' if reference.get('datepicker') else 'MISSING'}, "
          f"drop-lists {reference.get('dropLists', 0)}, "
          f"hotspots found: {reference.get('results') or '?'}, "
          f"canvases: {reference.get('hotspotCanvases', 0)}, "
          f"painted at {painted}/{len(results)} widths")

    failed_checks = [check for check in checks if not check.get('ok')]
    if checks:
        print("\ntime slider:")
        for check in checks:
            detail = f"  ({check['detail']})" if check.get('detail') else ""
            print(f"  {'ok  ' if check['ok'] else 'FAIL'}  {check['name']}{detail}")

    if errors:
        print(f"\njavascript errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    if failed or errors or failed_checks or not checks:
        print(f"\nFAILED: {len(failed)} width(s) overflow, {len(errors)} javascript error(s), "
              + (f"{len(failed_checks)} time slider check(s) failed" if checks
                 else "and the time slider checks did not run at all"))
        return False

    print(f"\nOK: no horizontal overflow at any of the {len(results)} widths, "
          f"no javascript errors, {len(checks)} time slider checks passed")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, help="port for the development server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--browser", help="browser binary to use (default: firefox, then chromium)")
    parser.add_argument("--url", help="check an already running server instead of starting one")
    parser.add_argument("--timeout", type=int, default=150, help="seconds to wait for the browser")
    options = parser.parse_args()

    browser, kind = find_browser(options.browser)
    if not browser:
        print("no headless browser found (tried firefox and chromium).\n"
              "install one, or run the check by hand: open /_dev/responsive/ in a browser.")
        return 2

    server = None
    base_url = options.url.rstrip("/") if options.url else f"http://{options.host}:{options.port}"

    if not options.url:
        if port_is_open(options.host, options.port):
            if not clear_report(base_url):
                print(f"{options.host}:{options.port} is taken by something that is not this "
                      f"project's development server.\nStop it, or use another port: "
                      f"make check-responsive PORT=8010")
                return 2
            print(f"reusing the server already listening on {options.host}:{options.port}")
        else:
            server = start_server(options.host, options.port)
            if server is None:
                return 2
            clear_report(base_url)
    else:
        clear_report(base_url)
    profile_dir = prepare_profile(kind)
    command = browser_command(browser, kind, f"{base_url}/_dev/responsive/", profile_dir)
    print(f"checking {base_url}/ with {Path(browser).name} (headless), "
          f"this takes about half a minute…")

    browser_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        report = poll_report(base_url, timeout=options.timeout)
    finally:
        browser_process.terminate()
        try:
            browser_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            browser_process.kill()
        if server:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
            Path(server.log_path).unlink(missing_ok=True)

    if report is None:
        print(f"the browser did not report back within {options.timeout}s")
        return 2

    return 0 if print_report(report) else 1


if __name__ == "__main__":
    sys.exit(main())
