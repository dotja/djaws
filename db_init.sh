python manage.py makemigrations
python manage.py migrate --no-input
python manage.py collectstatic --no-input

gunicorn myproject.wsgi:application --bind 0.0.0.0:8000