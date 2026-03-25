import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Andrea_jimenez.settings')
django.setup()
from configuraciones.models import Prenda
from django.core.files.storage import default_storage

try:
    p = Prenda.objects.get(codigo_barras='AJ-000001')
    print(f'Nombre: {p.nombre}')
    print(f'Imagen: {p.imagen.name if p.imagen else "N/A"}')
    print(f'Barcode: {p.barcode_image.name if p.barcode_image else "N/A"}')
    if p.imagen:
        print(f'Imagen URL: {p.imagen.url}')
        print(f'Imagen existe: {default_storage.exists(p.imagen.name)}')
    if p.barcode_image:
        print(f'Barcode URL: {p.barcode_image.url}')
        print(f'Barcode existe: {default_storage.exists(p.barcode_image.name)}')
        
    print(f'MEDIA_URL: {django.conf.settings.MEDIA_URL}')
    print(f'MEDIA_ROOT: {django.conf.settings.MEDIA_ROOT}')
    
except Exception as e:
    print(f'Error: {e}')
