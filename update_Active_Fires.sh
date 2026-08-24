#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/activefires/apps/Active_Fires"
cd "$PROJECT_DIR"

# manage.py defaults to the production settings module, which refuses to start
# without DJANGO_SECRET_KEY. uwsgi reads it through EnvironmentFile and the
# crontabs source it the same way; collectstatic below runs in this shell.
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -r "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE is missing or unreadable; DJANGO_SECRET_KEY comes from it." >&2
    exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

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
