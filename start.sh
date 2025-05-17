release: python manage.py migrate
web: gunicorn tienda.wsgi