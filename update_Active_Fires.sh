#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/activefires/apps/Active_Fires"
cd "$PROJECT_DIR"

echo "=== Pulling latest changes ==="
git fetch
git pull --ff-only

echo ""
echo "=== Last commit ==="
git log -1 --oneline

echo ""
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo ""
echo "=== Restarting uWSGI ==="
sudo systemctl reload uwsgi || sudo systemctl restart uwsgi

echo ""
echo "Update finished"
