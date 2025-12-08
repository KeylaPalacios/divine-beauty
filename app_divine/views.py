from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db.models import Sum
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.templatetags.static import static
from django.urls import reverse

from .forms import (
    FormularioCabello,
    FormularioCuidadoPiel,
    FormularioInicioSesion,
    FormularioMaquillaje,
    FormularioPago,
    FormularioPerfume,
    FormularioRegistro,
    FormularioUsuarioAdmin,
)
from .models import Cabello, CuidadoPiel, Maquillaje, Pedido, Perfume, Usuario

IMPUESTO_PORCENTAJE = Decimal("0.16")
COSTO_ENVIO = Decimal("120.00")

MAPA_MODELOS = {
    "cabello": (Cabello, "Cabello"),
    "maquillaje": (Maquillaje, "Maquillaje"),
    "cuidado": (CuidadoPiel, "Cuidado de la piel"),
    "perfumes": (Perfume, "Perfumes"),
}


def resolver_imagen(ruta):
    if not ruta:
        return static("imagenes/placeholder.png")
    return static(ruta)


def construir_producto(instancia, tipo_slug, etiqueta):
    # Obtener la URL de la imagen si existe
    imagen_url = None
    if instancia.foto and hasattr(instancia.foto, 'url'):
        imagen_url = instancia.foto.url
    elif instancia.foto:
        # Si es una cadena (ruta antigua)
        imagen_url = instancia.foto
    else:
        # Imagen por defecto si no hay foto
        imagen_url = "/static/imagenes/placeholder.png"

    return {
        "id": instancia.id,
        "nombre": instancia.nombre,
        "descripcion": instancia.descripcion,
        "precio": str(instancia.precio),  # Convertir a string para el carrito
        "stock": instancia.stock,
        "categoria": etiqueta,
        "tipo_slug": tipo_slug,
        "imagen": imagen_url,
    }


def recolectar_productos(categoria_slug="todos"):
    productos = []
    if categoria_slug == "todos":
        for slug, (modelo, etiqueta) in MAPA_MODELOS.items():
            for articulo in modelo.objects.all():
                productos.append(construir_producto(articulo, slug, etiqueta))
    else:
        datos = MAPA_MODELOS.get(categoria_slug)
        if datos:
            modelo, etiqueta = datos
            for articulo in modelo.objects.all():
                productos.append(construir_producto(articulo, categoria_slug, etiqueta))
    return productos


def traer_carrito(request):
    return request.session.get("carrito", {})


def guardar_carrito(request, carrito):
    request.session["carrito"] = carrito
    request.session.modified = True


def requiere_login(funcion):
    @wraps(funcion)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("usuario_id"):
            messages.warning(request, "Debes iniciar sesión para continuar.")
            return redirect("iniciar_sesion")
        return funcion(request, *args, **kwargs)

    return envoltura


def requiere_admin(funcion):
    @wraps(funcion)
    def envoltura(request, *args, **kwargs):
        usuario_id = request.session.get("usuario_id")
        if not usuario_id:
            messages.warning(request, "Debes iniciar sesión para continuar.")
            return redirect("iniciar_sesion")
        try:
            usuario = Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            request.session.flush()
            return redirect("iniciar_sesion")
        if not usuario.es_admin:
            messages.error(request, "No tienes permisos para entrar al panel.")
            return redirect("inicio")
        return funcion(request, *args, **kwargs)

    return envoltura


def obtener_usuario(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return None
    try:
        return Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        request.session.flush()
        return None


def inicio(request):
    carrusel = [
        {
            "titulo": "Cabello radiante",
            "categoria_slug": "cabello",
            "imagen": resolver_imagen("imagenes/cabello.jpg"),
        },
        {
            "titulo": "Maquillaje creativo",
            "categoria_slug": "maquillaje",
            "imagen": resolver_imagen("imagenes/maquillaje.jpg"),
        },
        {
            "titulo": "Cuidado de la piel",
            "categoria_slug": "cuidado",
            "imagen": resolver_imagen("imagenes/piel.jpg"),
        },
        {
            "titulo": "Perfumes exclusivos",
            "categoria_slug": "perfumes",
            "imagen": resolver_imagen("imagenes/perfume.jpg"),
        },
    ]
    destacados = []
    for slug, (modelo, etiqueta) in MAPA_MODELOS.items():
        articulo = modelo.objects.order_by("-id").first()
        if articulo:
            destacados.append(construir_producto(articulo, slug, etiqueta))
    contexto = {
        "carrusel": carrusel,
        "destacados": destacados,
        "novedades_banner": resolver_imagen("imagenes/novedades.jpg"),
    }
    return render(request, "usuario/index.html", contexto)


def novedades(request):
    productos = recolectar_productos("todos")
    productos = sorted(productos, key=lambda x: x["id"], reverse=True)[:12]
    return render(
        request,
        "usuario/novedades.html",
        {"productos": productos, "categoria_legible": "Novedades"},
    )


def productos(request):
    categoria = request.GET.get("categoria", "todos")
    if categoria not in MAPA_MODELOS and categoria != "todos":
        categoria = "todos"
    listado = recolectar_productos(categoria)
    mapa_legible = {
        "todos": "Todos los productos",
        "cabello": "Cabello",
        "maquillaje": "Maquillaje",
        "cuidado": "Cuidado de la piel",
        "perfumes": "Perfumes",
    }
    contexto = {
        "productos": listado,
        "categoria_actual": categoria,
        "categoria_legible": mapa_legible.get(categoria, "Todos los productos"),
    }
    return render(request, "usuario/productos.html", contexto)


def detalle_producto(request, tipo, pk):
    datos = MAPA_MODELOS.get(tipo)
    if not datos:
        messages.error(request, "Producto no encontrado.")
        return redirect("productos")
    modelo, etiqueta = datos
    producto = get_object_or_404(modelo, pk=pk)
    contexto = {
        "producto": construir_producto(producto, tipo, etiqueta),
    }
    return render(request, "usuario/detalle_producto.html", contexto)


@requiere_login
def agregar_carrito(request, tipo, pk):
    if request.method != "POST":
        return redirect("detalle_producto", tipo=tipo, pk=pk)
    datos = MAPA_MODELOS.get(tipo)
    if not datos:
        messages.error(request, "Producto no disponible.")
        return redirect("productos")
    modelo, etiqueta = datos
    producto = get_object_or_404(modelo, pk=pk)
    cantidad = request.POST.get("cantidad", "1")
    try:
        cantidad = int(cantidad)
        if cantidad < 1:
            cantidad = 1
    except ValueError:
        cantidad = 1
    carrito = traer_carrito(request)
    clave = f"{tipo}-{pk}"
    
    # Construir el producto con todos los datos incluyendo la imagen
    producto_data = construir_producto(producto, tipo, etiqueta)
    
    if clave in carrito:
        carrito[clave]["cantidad"] += cantidad
    else:
        carrito[clave] = {
            "nombre": producto_data["nombre"],
            "precio": producto_data["precio"],
            "cantidad": cantidad,
            "tipo": tipo,
            "producto_id": producto.id,
            "imagen": producto_data["imagen"],  # Asegurar que la imagen se guarda
            "categoria": producto_data["categoria"],
        }
    guardar_carrito(request, carrito)
    messages.success(request, f"{producto.nombre} se agregó al carrito.")
    return redirect("carrito")


@requiere_login
def ver_carrito(request):
    carrito = traer_carrito(request)
    items = []
    subtotal = Decimal("0.00")
    for clave, item in carrito.items():
        precio = Decimal(item["precio"])
        cantidad = item["cantidad"]
        total_linea = precio * cantidad
        subtotal += total_linea
        items.append(
            {
                "clave": clave,
                "nombre": item["nombre"],
                "precio": precio,
                "cantidad": cantidad,
                "total_linea": total_linea,
                "imagen": item["imagen"],
            }
        )
    impuestos = subtotal * IMPUESTO_PORCENTAJE
    total = subtotal + impuestos + (COSTO_ENVIO if items else Decimal("0.00"))
    contexto = {
        "items": items,
        "subtotal": subtotal,
        "impuestos": impuestos,
        "envio": COSTO_ENVIO if items else Decimal("0.00"),
        "total": total,
    }
    return render(request, "usuario/carrito.html", contexto)


@requiere_login
def actualizar_carrito(request):
    if request.method != "POST":
        return redirect("carrito")
    carrito = traer_carrito(request)
    for clave in list(carrito.keys()):
        campo = f"cantidad_{clave}"
        if campo in request.POST:
            try:
                cantidad = int(request.POST.get(campo))
            except (ValueError, TypeError):
                cantidad = carrito[clave]["cantidad"]
            if cantidad < 1:
                del carrito[clave]
            else:
                carrito[clave]["cantidad"] = cantidad
    guardar_carrito(request, carrito)
    messages.success(request, "Se actualizó el carrito.")
    return redirect("carrito")


@requiere_login
def eliminar_item_carrito(request, clave):
    carrito = traer_carrito(request)
    if clave in carrito:
        del carrito[clave]
        guardar_carrito(request, carrito)
        messages.success(request, "Producto eliminado del carrito.")
    return redirect("carrito")


@requiere_login
def procesar_pago(request):
    carrito = traer_carrito(request)
    if not carrito:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("productos")
    subtotal = Decimal("0.00")
    detalle_lineas = []
    for item in carrito.values():
        precio = Decimal(item["precio"])
        cantidad = item["cantidad"]
        total_linea = precio * cantidad
        subtotal += total_linea
        detalle_lineas.append(
            f"{item['nombre']} x{cantidad} - ${total_linea}"
        )
    impuestos = subtotal * IMPUESTO_PORCENTAJE
    total = subtotal + impuestos + COSTO_ENVIO
    usuario = obtener_usuario(request)
    if not usuario:
        return redirect("iniciar_sesion")
    if request.method == "POST":
        formulario = FormularioPago(request.POST)
        if formulario.is_valid():
            metodo = formulario.cleaned_data["metodo"]
            domicilio = formulario.cleaned_data["domicilio"]
            if metodo == "tarjeta":
                necesarios = [
                    formulario.cleaned_data.get("nombre_tarjeta"),
                    formulario.cleaned_data.get("numero_tarjeta"),
                    formulario.cleaned_data.get("mes_vencimiento"),
                    formulario.cleaned_data.get("anio_vencimiento"),
                    formulario.cleaned_data.get("cvv"),
                ]
                if not all(necesarios):
                    messages.error(
                        request,
                        "Completa todos los datos de la tarjeta para continuar.",
                    )
                    return redirect("procesar_pago")
            if metodo == "paypal":
                if not formulario.cleaned_data.get("correo_paypal"):
                    messages.error(
                        request,
                        "Ingresa el correo de PayPal para continuar.",
                    )
                    return redirect("procesar_pago")
            detalle_lineas.append(f"Impuestos: ${impuestos}")
            detalle_lineas.append(f"Envío: ${COSTO_ENVIO}")
            detalle_lineas.append(f"Total: ${total}")
            detalle = "\n".join(detalle_lineas)
            Pedido.objects.create(
                id_usuario=usuario,
                subtotal=subtotal,
                formapago=metodo,
                envio=COSTO_ENVIO,
                domicilio=domicilio,
                detalle=detalle,
            )
            guardar_carrito(request, {})
            messages.success(
                request,
                "¡Gracias! Tu compra fue completada correctamente.",
            )
            return redirect("perfil_usuario")
    else:
        formulario = FormularioPago()
    contexto = {
        "formulario": formulario,
        "subtotal": subtotal,
        "impuestos": impuestos,
        "envio": COSTO_ENVIO,
        "total": total,
    }
    return render(request, "usuario/pago.html", contexto)


@requiere_login
def perfil_usuario(request):
    usuario = obtener_usuario(request)
    pedidos = usuario.pedidos.order_by("-fecha_creacion")
    return render(
        request,
        "usuario/perfil.html",
        {"usuario": usuario, "pedidos": pedidos},
    )


def contacto(request):
    return render(request, "usuario/contacto.html")


def iniciar_sesion(request):
    if request.session.get("usuario_id"):
        return redirect("inicio")
    if request.method == "POST":
        formulario = FormularioInicioSesion(request.POST)
        if formulario.is_valid():
            correo = formulario.cleaned_data["correo_electronico"]
            contrasena = formulario.cleaned_data["contrasena"]
            try:
                usuario = Usuario.objects.get(correo_electronico=correo)
            except Usuario.DoesNotExist:
                messages.error(request, "Credenciales no válidas.")
            else:
                if check_password(contrasena, usuario.contrasena):
                    request.session["usuario_id"] = usuario.id
                    messages.success(request, "Bienvenido de nuevo.")
                    return redirect("inicio")
                messages.error(request, "Credenciales no válidas.")
    else:
        formulario = FormularioInicioSesion()
    return render(
        request,
        "usuario/iniciar_sesion.html",
        {"formulario": formulario},
    )


def cerrar_sesion(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada.")
    return redirect("inicio")


def registrarse(request):
    if request.session.get("usuario_id"):
        return redirect("inicio")
    if request.method == "POST":
        formulario = FormularioRegistro(request.POST)
        if formulario.is_valid():
            usuario = formulario.save()
            request.session["usuario_id"] = usuario.id
            messages.success(request, "Registro exitoso, bienvenido.")
            return redirect("inicio")
    else:
        formulario = FormularioRegistro()
    return render(
        request,
        "usuario/registrarse.html",
        {"formulario": formulario},
    )


@requiere_admin
def panel_admin(request):
    contexto = {
        "total_cabello": Cabello.objects.count(),
        "total_maquillaje": Maquillaje.objects.count(),
        "total_piel": CuidadoPiel.objects.count(),
        "total_perfumes": Perfume.objects.count(),
        "total_usuarios": Usuario.objects.count(),
        "total_pedidos": Pedido.objects.count(),
        "ingresos": Pedido.objects.aggregate(total=Sum("subtotal"))["total"]
        or Decimal("0.00"),
    }
    return render(request, "admin/panel.html", contexto)


@requiere_admin
def admin_cabello_lista(request):
    articulos = Cabello.objects.all()
    return render(
        request,
        "admin/cabello_lista.html",
        {"articulos": articulos},
    )


@requiere_admin
def admin_cabello_crear(request):
    if request.method == "POST":
        formulario = FormularioCabello(request.POST, request.FILES)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto de Cabello creado.")
            return redirect("admin_cabello_lista")
    else:
        formulario = FormularioCabello()
    return render(
        request,
        "admin/cabello_form.html",
        {"formulario": formulario, "titulo_form": "Nuevo producto de Cabello"},
    )


@requiere_admin
def admin_cabello_editar(request, pk):
    articulo = get_object_or_404(Cabello, pk=pk)
    if request.method == "POST":
        formulario = FormularioCabello(request.POST, request.FILES, instance=articulo)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto de Cabello actualizado.")
            return redirect("admin_cabello_lista")
    else:
        formulario = FormularioCabello(instance=articulo)
    return render(
        request,
        "admin/cabello_form.html",
        {"formulario": formulario, "titulo_form": "Editar producto de Cabello"},
    )


@requiere_admin
def admin_cabello_eliminar(request, pk):
    articulo = get_object_or_404(Cabello, pk=pk)
    if request.method == "POST":
        articulo.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("admin_cabello_lista")
    return render(
        request,
        "admin/confirmar_eliminacion.html",
        {
            "objeto": articulo,
            "titulo": "Eliminar producto de Cabello",
            "url_cancelar": reverse("admin_cabello_lista"),
        },
    )


@requiere_admin
def admin_maquillaje_lista(request):
    articulos = Maquillaje.objects.all()
    return render(
        request,
        "admin/maquillaje_lista.html",
        {"articulos": articulos},
    )


@requiere_admin
def admin_maquillaje_crear(request):
    if request.method == "POST":
        formulario = FormularioMaquillaje(request.POST, request.FILES)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto de Maquillaje creado.")
            return redirect("admin_maquillaje_lista")
    else:
        formulario = FormularioMaquillaje()
    return render(
        request,
        "admin/maquillaje_form.html",
        {"formulario": formulario, "titulo_form": "Nuevo Maquillaje"},
    )


@requiere_admin
def admin_maquillaje_editar(request, pk):
    articulo = get_object_or_404(Maquillaje, pk=pk)
    if request.method == "POST":
        formulario = FormularioMaquillaje(request.POST, request.FILES, instance=articulo)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto de Maquillaje actualizado.")
            return redirect("admin_maquillaje_lista")
    else:
        formulario = FormularioMaquillaje(instance=articulo)
    return render(
        request,
        "admin/maquillaje_form.html",
        {"formulario": formulario, "titulo_form": "Editar Maquillaje"},
    )


@requiere_admin
def admin_maquillaje_eliminar(request, pk):
    articulo = get_object_or_404(Maquillaje, pk=pk)
    if request.method == "POST":
        articulo.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("admin_maquillaje_lista")
    return render(
        request,
        "admin/confirmar_eliminacion.html",
        {
            "objeto": articulo,
            "titulo": "Eliminar producto de Maquillaje",
            "url_cancelar": reverse("admin_maquillaje_lista"),
        },
    )


@requiere_admin
def admin_piel_lista(request):
    articulos = CuidadoPiel.objects.all()
    return render(
        request,
        "admin/piel_lista.html",
        {"articulos": articulos},
    )


@requiere_admin
def admin_piel_crear(request):
    if request.method == "POST":
        formulario = FormularioCuidadoPiel(request.POST, request.FILES)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto de Cuidado de la piel creado.")
            return redirect("admin_piel_lista")
    else:
        formulario = FormularioCuidadoPiel()
    return render(
        request,
        "admin/piel_form.html",
        {"formulario": formulario, "titulo_form": "Nuevo Cuidado de la piel"},
    )


@requiere_admin
def admin_piel_editar(request, pk):
    articulo = get_object_or_404(CuidadoPiel, pk=pk)
    if request.method == "POST":
        formulario = FormularioCuidadoPiel(request.POST, request.FILES, instance=articulo)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Producto de Cuidado de la piel actualizado.")
            return redirect("admin_piel_lista")
    else:
        formulario = FormularioCuidadoPiel(instance=articulo)
    return render(
        request,
        "admin/piel_form.html",
        {"formulario": formulario, "titulo_form": "Editar Cuidado de la piel"},
    )


@requiere_admin
def admin_piel_eliminar(request, pk):
    articulo = get_object_or_404(CuidadoPiel, pk=pk)
    if request.method == "POST":
        articulo.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("admin_piel_lista")
    return render(
        request,
        "admin/confirmar_eliminacion.html",
        {
            "objeto": articulo,
            "titulo": "Eliminar producto de Cuidado de la piel",
            "url_cancelar": reverse("admin_piel_lista"),
        },
    )


@requiere_admin
def admin_perfumes_lista(request):
    articulos = Perfume.objects.all()
    return render(
        request,
        "admin/perfumes_lista.html",
        {"articulos": articulos},
    )


@requiere_admin
def admin_perfumes_crear(request):
    if request.method == "POST":
        formulario = FormularioPerfume(request.POST, request.FILES)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Perfume creado.")
            return redirect("admin_perfumes_lista")
    else:
        formulario = FormularioPerfume()
    return render(
        request,
        "admin/perfumes_form.html",
        {"formulario": formulario, "titulo_form": "Nuevo Perfume"},
    )


@requiere_admin
def admin_perfumes_editar(request, pk):
    articulo = get_object_or_404(Perfume, pk=pk)
    if request.method == "POST":
        formulario = FormularioPerfume(request.POST, request.FILES, instance=articulo)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Perfume actualizado.")
            return redirect("admin_perfumes_lista")
    else:
        formulario = FormularioPerfume(instance=articulo)
    return render(
        request,
        "admin/perfumes_form.html",
        {"formulario": formulario, "titulo_form": "Editar Perfume"},
    )


@requiere_admin
def admin_perfumes_eliminar(request, pk):
    articulo = get_object_or_404(Perfume, pk=pk)
    if request.method == "POST":
        articulo.delete()
        messages.success(request, "Perfume eliminado.")
        return redirect("admin_perfumes_lista")
    return render(
        request,
        "admin/confirmar_eliminacion.html",
        {
            "objeto": articulo,
            "titulo": "Eliminar Perfume",
            "url_cancelar": reverse("admin_perfumes_lista"),
        },
    )


@requiere_admin
def admin_usuarios_lista(request):
    usuarios = Usuario.objects.all()
    return render(
        request,
        "admin/usuarios_lista.html",
        {"usuarios": usuarios},
    )


@requiere_admin
def admin_usuarios_crear(request):
    if request.method == "POST":
        formulario = FormularioUsuarioAdmin(request.POST)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Usuario creado.")
            return redirect("admin_usuarios_lista")
    else:
        formulario = FormularioUsuarioAdmin()
    return render(
        request,
        "admin/usuarios_form.html",
        {"formulario": formulario, "titulo_form": "Nuevo usuario"},
    )


@requiere_admin
def admin_usuarios_editar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        formulario = FormularioUsuarioAdmin(request.POST, instance=usuario)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "Usuario actualizado.")
            return redirect("admin_usuarios_lista")
    else:
        formulario = FormularioUsuarioAdmin(instance=usuario)
    return render(
        request,
        "admin/usuarios_form.html",
        {"formulario": formulario, "titulo_form": "Editar usuario"},
    )


@requiere_admin
def admin_usuarios_eliminar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        usuario.delete()
        messages.success(request, "Usuario eliminado.")
        return redirect("admin_usuarios_lista")
    return render(
        request,
        "admin/confirmar_eliminacion.html",
        {
            "objeto": usuario,
            "titulo": "Eliminar usuario",
            "url_cancelar": reverse("admin_usuarios_lista"),
        },
    )


@requiere_admin
def admin_usuario_detalle(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    pedidos = usuario.pedidos.order_by("-fecha_creacion")
    return render(
        request,
        "admin/usuario_detalle.html",
        {"usuario": usuario, "pedidos": pedidos},
    )


@requiere_admin
def admin_pedidos_lista(request):
    pedidos = Pedido.objects.select_related("id_usuario").order_by("-fecha_creacion")
    return render(
        request,
        "admin/pedidos_lista.html",
        {"pedidos": pedidos},
    )