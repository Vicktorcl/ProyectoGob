import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')
application = get_wsgi_application()

# —————— AUTO-MIGRATE ON STARTUP ——————
from django.core.management import call_command
from django.db.utils import OperationalError

try:
    call_command('migrate', interactive=False)
except OperationalError:
    # La DB aún no está lista; lo ignoramos
    pass

# —————— AUTO-CREATE SUPERUSER ON STARTUP ——————
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and password:
    try:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email or '',
                password=password
            )
    except OperationalError:
        # Si la BD no está lista o hay otro error, lo ignoramos
        pass
