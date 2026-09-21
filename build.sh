#!/usr/bin/env bash
set -o errexit

echo "=== Paketlar o'rnatilmoqda ==="
pip install -r requirements.txt

echo "=== Statik fayllar to'planmoqda ==="
python manage.py collectstatic --noinput

echo "=== Migratsiyalar bajarilmoqda ==="
python manage.py migrate --noinput

echo "=== Boshlang'ich test ma'lumotlari yaratilmoqda ==="
python manage.py seed_data
