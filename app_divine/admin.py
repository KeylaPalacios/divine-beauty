from django.contrib import admin
from .models import Cabello, Maquillaje, CuidadoPiel, Perfume, Usuario, Pedido


@admin.register(Cabello)
class CabelloAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")


@admin.register(Maquillaje)
class MaquillajeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")


@admin.register(CuidadoPiel)
class CuidadoPielAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "categoria")


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "correo_electronico", "es_admin")
    search_fields = ("nombre", "apellido", "correo_electronico")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id_usuario", "subtotal", "formapago", "envio", "fecha_creacion")
    list_filter = ("formapago", "fecha_creacion")