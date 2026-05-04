#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
# No migrations for MongoDB usually, but keep for SQLite if used
python manage.py migrate --no-input
