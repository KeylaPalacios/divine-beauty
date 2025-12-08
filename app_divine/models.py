from decimal import Decimal
from django.db import models
from django.utils import timezone


class ProductoBase(models.Model):
    stock = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    categoria = models.CharField(max_length=80)
    foto = models.ImageField(upload_to='productos/', blank=True, null=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField()

    class Meta:
        abstract = True


class Cabello(ProductoBase):
    class Meta:
        db_table = "cabello"

    def __str__(self):
        return self.nombre


class Maquillaje(ProductoBase):
    class Meta:
        db_table = "maquillaje"

    def __str__(self):
        return self.nombre


class CuidadoPiel(ProductoBase):
    class Meta:
        db_table = "cuidado_de_la_piel"

    def __str__(self):
        return self.nombre


class Perfume(ProductoBase):
    class Meta:
        db_table = "perfumes"

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    fecha_nacimiento = models.DateField()
    correo_electronico = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=128)
    direccion = models.TextField()
    es_admin = models.BooleanField(default=False)

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Pedido(models.Model):
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="pedidos"
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    formapago = models.CharField(max_length=60)
    envio = models.DecimalField(max_digits=10, decimal_places=2)
    domicilio = models.TextField()
    detalle = models.TextField()
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk} - {self.id_usuario}"