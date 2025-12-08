from .models import Usuario

def usuario_en_sesion(request):
    usuario = None
    usuario_id = request.session.get("usuario_id")
    if usuario_id:
        try:
            usuario = Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            request.session.flush()
    return {"usuario_en_sesion": usuario}