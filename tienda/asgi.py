import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')
application = get_asgi_application()

# —————— AUTO-MIGRATE ON STARTUP ——————
from django.core.management import call_command
from django.db.utils import OperationalError

try:
    # Aplica las migraciones pendientes sin pedir interacción
    call_command('migrate', interactive=False)
except OperationalError:
    # La base de datos aún no está lista: lo ignoramos y seguimos.
    pass
