import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Andrea_jimenez.settings')
django.setup()

from configuraciones.models import Prenda

print("--- Checking Prenda Images ---")
for p in Prenda.objects.all()[:10]:
    img_path = p.imagen.url if p.imagen else "NO IMAGE"
    barcode_path = p.barcode_image.url if p.barcode_image else "NO BARCODE"
    print(f"ID {p.id} - {p.nombre}: Image={img_path}, Barcode={barcode_path}")
