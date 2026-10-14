#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install production dependencies
pip install -r requirements.txt

# Collect static files into STATIC_ROOT
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
