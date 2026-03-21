import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Andrea_jimenez.settings")
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User

# Si no hay usuarios en produccion, asumimos que la DB esta recien creada
if User.objects.count() == 0:
    print(">>> Base de datos vacia detectada. Cargando el archivo backup_render.json...")
    try:
        call_command("loaddata", "backup_render.json")
        print(">>> Backup cargado exitosamente.")
    except Exception as e:
        print(f">>> Error cargando el backup: {e}")
else:
    print(">>> La base de datos ya tiene informacion. Se ignora la restauracion para proteger el progreso actual.")
