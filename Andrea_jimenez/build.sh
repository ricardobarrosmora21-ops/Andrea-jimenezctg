#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Cargar automaticamente la copia de seguridad si estamos en plan gratis
python load_initial_data.py
