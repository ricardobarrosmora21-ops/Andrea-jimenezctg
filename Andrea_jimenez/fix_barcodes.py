import os
import django
from io import BytesIO
from django.core.files import File
import barcode
from barcode.writer import ImageWriter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Andrea_jimenez.settings')
django.setup()

from configuraciones.models import Prenda, VariacionPrenda

def regenerate_barcodes():
    print("Regenerating Prenda barcodes...")
    for prenda in Prenda.objects.all():
        if prenda.codigo_barras:
            print(f"  Processing {prenda.nombre} ({prenda.codigo_barras})...")
            COD128 = barcode.get_barcode_class('code128')
            rv = BytesIO()
            code = COD128(prenda.codigo_barras, writer=ImageWriter())
            code.write(rv, options={"module_height": 15.0, "font_size": 12, "text_distance": 5.0, "quiet_zone": 6.0})
            
            filename = f"barcode-{prenda.codigo_barras}.png"
            rv.seek(0)
            
            # Use a slightly different name or force overwrite if possible
            # Actually, we can just save it. Django will handle name collisions or overwrite if configured.
            prenda.barcode_image.save(filename, File(rv), save=True)
            print(f"    Saved as: {prenda.barcode_image.name}")

    print("\nRegenerating VariacionPrenda barcodes...")
    for v in VariacionPrenda.objects.all():
        if v.codigo_barras:
            print(f"  Processing {v.prenda.nombre} - {v.talla} ({v.codigo_barras})...")
            COD128 = barcode.get_barcode_class('code128')
            rv = BytesIO()
            code = COD128(v.codigo_barras, writer=ImageWriter())
            code.write(rv, options={"module_height": 10.0, "font_size": 10, "text_distance": 4.0, "quiet_zone": 5.0})
            
            filename = f"barcode-v-{v.codigo_barras}.png"
            rv.seek(0)
            v.barcode_image.save(filename, File(rv), save=True)
            print(f"    Saved as: {v.barcode_image.name}")

if __name__ == "__main__":
    regenerate_barcodes()
