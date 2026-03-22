from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.files import File
from io import BytesIO
import barcode
from barcode.writer import ImageWriter


# =====================================================================
#  USUARIOS
# =====================================================================

class Cliente(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() if self.user else f"Cliente #{self.id}"


class Administrador(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    rol = models.CharField(max_length=50, default='Administrador')

    def __str__(self):
        return self.user.get_full_name() if self.user else f"Administrador #{self.id}"


# =====================================================================
#  CATEGORÍAS Y PRENDAS
# =====================================================================

class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default='Sin nombre')

    def __str__(self):
        return self.nombre


class Inventario(models.Model):
    id = models.AutoField(primary_key=True)
    cantidad_actual = models.PositiveIntegerField(default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.SET_NULL,
        related_name='inventarios',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Inventario #{self.id} ({self.cantidad_actual} unidades)"

    # Ajustes de inventario seguros
    def aumentar(self, cantidad):
        self.cantidad_actual = models.F('cantidad_actual') + int(cantidad)
        self.save(update_fields=["cantidad_actual"])
        self.refresh_from_db()

    def disminuir(self, cantidad):
        cantidad = int(cantidad)
        if self.cantidad_actual >= cantidad:
            self.cantidad_actual = models.F('cantidad_actual') - cantidad
            self.save(update_fields=["cantidad_actual"])
            self.refresh_from_db()
            return True
        return False

    @property
    def disponible(self):
        return max(self.cantidad_actual, 0)


class Prenda(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, default="Sin nombre")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    precio_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Stock directo + relación con inventario
    stock = models.IntegerField(default=0)
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.SET_NULL,
        related_name="prendas",
        null=True,
        blank=True
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        related_name="prendas",
        null=True,
        blank=True
    )
    imagen = models.ImageField(upload_to="productos/", null=True, blank=True)
    codigo_barras = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    barcode_image = models.ImageField(upload_to="barcodes/", null=True, blank=True)

    # Destacados
    es_destacado = models.BooleanField(default=False)

    # Soft delete profesional
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["nombre"]),
            models.Index(fields=["is_archived"]),
        ]

    def save(self, *args, **kwargs):
        # 1. Asignar slug único automáticamente
        if not self.slug:
            base = slugify(self.nombre)[:110]
            slug = base
            counter = 1
            while Prenda.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug

        # 2. Guardado inicial para obtener ID (si es nuevo)
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 3. Generar código de barras si no existe
        if not self.codigo_barras:
            self.codigo_barras = f"AJ-{self.id:06d}"
            # Actualizamos sin llamar de nuevo al save completo
            Prenda.objects.filter(id=self.id).update(codigo_barras=self.codigo_barras)

        # 4. Generar imagen del código de barras si no existe
        if self.codigo_barras and not self.barcode_image:
            COD128 = barcode.get_barcode_class('code128')
            rv = BytesIO()
            # Altura de 15mm para una imagen base más grande y clara
            code = COD128(self.codigo_barras, writer=ImageWriter())
            code.write(rv, options={"module_height": 15.0, "font_size": 12, "text_distance": 5.0, "quiet_zone": 6.0})
            
            # Guardamos la imagen
            filename = f"barcode-{self.codigo_barras}.png"
            rv.seek(0)
            self.barcode_image.save(filename, File(rv), save=False)
            # Actualizamos solo la imagen
            Prenda.objects.filter(id=self.id).update(barcode_image=self.barcode_image.name)

    def archive(self):
        """Arquiva sin borrar datos"""
        if not self.is_archived:
            self.is_archived = True
            self.archived_at = timezone.now()
            super().save(update_fields=["is_archived", "archived_at"])

    def restore(self):
        """Restaura producto archivado"""
        if self.is_archived:
            self.is_archived = False
            self.archived_at = None
            super().save(update_fields=["is_archived", "archived_at"])

    def __str__(self):
        return self.nombre


class VariacionPrenda(models.Model):
    id = models.AutoField(primary_key=True)
    prenda = models.ForeignKey(Prenda, on_delete=models.CASCADE, related_name="variaciones")
    talla = models.CharField(max_length=10, help_text="Ej: S, M, L, XL")
    color = models.CharField(max_length=50, help_text="Ej: Rojo, Azul, Negro", null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    codigo_barras = models.CharField(max_length=50, unique=True, null=True, blank=True)
    barcode_image = models.ImageField(upload_to="barcodes/variaciones/", null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generar código de barras si no existe
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.codigo_barras:
            self.codigo_barras = f"AJ-V{self.id:06d}"
            VariacionPrenda.objects.filter(id=self.id).update(codigo_barras=self.codigo_barras)

        if self.codigo_barras and not self.barcode_image:
            COD128 = barcode.get_barcode_class('code128')
            rv = BytesIO()
            code = COD128(self.codigo_barras, writer=ImageWriter())
            code.write(rv, options={"module_height": 10.0, "font_size": 10, "text_distance": 4.0, "quiet_zone": 5.0})
            filename = f"barcode-v-{self.codigo_barras}.png"
            rv.seek(0)
            self.barcode_image.save(filename, File(rv), save=False)
            VariacionPrenda.objects.filter(id=self.id).update(barcode_image=self.barcode_image.name)

    def __str__(self):
        return f"{self.prenda.nombre} - {self.talla} ({self.color or 'N/A'})"


# =====================================================================
#  CARRITO
# =====================================================================

class CarritoDeCompras(models.Model):
    id = models.AutoField(primary_key=True)
    cliente = models.OneToOneField(
        Cliente,
        on_delete=models.CASCADE,
        related_name="carrito",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Carrito de {self.cliente}" if self.cliente else "Carrito vacío"


class ItemCarrito(models.Model):
    id = models.AutoField(primary_key=True)
    carrito = models.ForeignKey(
        CarritoDeCompras,
        on_delete=models.CASCADE,
        related_name="items"
    )
    prenda = models.ForeignKey(
        Prenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    variacion = models.ForeignKey(
        VariacionPrenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        precio = self.prenda.precio_descuento if (self.prenda and self.prenda.precio_descuento) else (self.prenda.precio if self.prenda else 0)
        return precio * self.cantidad

    def __str__(self):
        desc = f"{self.prenda.nombre}" if self.prenda else "N/A"
        if self.variacion:
            desc += f" ({self.variacion.talla}/{self.variacion.color})"
        return f"{self.cantidad} x {desc}"


# =====================================================================
#  PEDIDOS / PAGOS / VENTAS
# =====================================================================

class Pedido(models.Model):
    ESTADOS = (
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
    )
    id = models.AutoField(primary_key=True)
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=50, choices=ESTADOS, default="Pendiente")
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        related_name="pedidos",
        null=True,
        blank=True
    )
    
    # Información de envío
    departamento = models.CharField(max_length=100, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    direccion_envio = models.TextField(null=True, blank=True)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    transportadora = models.CharField(max_length=100, null=True, blank=True)
    guia_rastreo = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.estado}"


class Pago(models.Model):
    id = models.AutoField(primary_key=True)
    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.SET_NULL,
        related_name="pago",
        null=True,
        blank=True
    )
    metodo = models.CharField(max_length=50, null=True, blank=True)
    estado = models.CharField(max_length=50, default="Pendiente")
    fecha = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Pago #{self.id}"


class CuponDescuento(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    porcentaje = models.PositiveIntegerField(help_text="0-100")
    activo = models.BooleanField(default=True)
    fecha_expiracion = models.DateTimeField()

    def es_valido(self):
        return self.activo and self.fecha_expiracion > timezone.now()

    def __str__(self):
        return f"{self.codigo} ({self.porcentaje}%)"


class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        related_name="ventas",
        null=True,
        blank=True
    )
    fecha_venta = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cupon = models.ForeignKey(CuponDescuento, on_delete=models.SET_NULL, null=True, blank=True)
    pago = models.OneToOneField(
        Pago,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        if self.cliente and self.cliente.user:
            return f"Venta #{self.id} - {self.cliente.user.username}"
        return f"Venta #{self.id} - Cliente N/A"


class DetalleVenta(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(
        Venta,
        on_delete=models.SET_NULL,
        related_name="detalles",
        null=True,
        blank=True
    )
    prenda = models.ForeignKey(Prenda, on_delete=models.SET_NULL, null=True, blank=True)
    variacion = models.ForeignKey(VariacionPrenda, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.prenda.nombre if self.prenda else 'N/A'}"
