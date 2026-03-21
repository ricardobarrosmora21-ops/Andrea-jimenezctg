import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Andrea_jimenez.settings')
django.setup()

from configuraciones.models import Prenda

with open('images_info.txt', 'w', encoding='utf-8') as f:
    for p in Prenda.objects.all():
        img = p.imagen.url if p.imagen else "None"
        bar = p.barcode_image.url if p.barcode_image else "None"
        f.write(f"ID: {p.id}, Nombre: {p.nombre}\n  Imagen: {img}\n  Barcode: {bar}\n\n")
