from django import forms
from django.contrib.auth.hashers import make_password

from .models import (
    Cabello,
    Maquillaje,
    CuidadoPiel,
    Perfume,
    Usuario,
)


class FormularioRegistro(forms.ModelForm):
    confirmar_contrasena = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "campo-texto"}),
    )

    class Meta:
        model = Usuario
        fields = [
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "correo_electronico",
            "direccion",
            "contrasena",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "campo-texto"}),
            "apellido": forms.TextInput(attrs={"class": "campo-texto"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "campo-texto"}
            ),
            "correo_electronico": forms.EmailInput(attrs={"class": "campo-texto"}),
            "direccion": forms.Textarea(attrs={"class": "campo-texto", "rows": 3}),
            "contrasena": forms.PasswordInput(attrs={"class": "campo-texto"}),
        }

    def clean(self):
        datos = super().clean()
        contrasena = datos.get("contrasena")
        confirmar = datos.get("confirmar_contrasena")
        if contrasena and confirmar and contrasena != confirmar:
            self.add_error("confirmar_contrasena", "Las contraseñas no coinciden.")
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.contrasena = make_password(self.cleaned_data["contrasena"])
        usuario.es_admin = False
        if commit:
            usuario.save()
        return usuario


class FormularioInicioSesion(forms.Form):
    correo_electronico = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "campo-texto"}),
    )
    contrasena = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "campo-texto"}),
    )


class FormularioCabello(forms.ModelForm):
    class Meta:
        model = Cabello
        fields = ["nombre", "descripcion", "precio", "stock", "categoria", "foto"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "campo-texto"}),
            "descripcion": forms.Textarea(attrs={"class": "campo-texto", "rows": 3}),
            "precio": forms.NumberInput(attrs={"class": "campo-texto", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "campo-texto"}),
            "categoria": forms.TextInput(attrs={"class": "campo-texto"}),
            "foto": forms.FileInput(attrs={"class": "campo-texto"}),
        }


class FormularioMaquillaje(forms.ModelForm):
    class Meta:
        model = Maquillaje
        fields = ["nombre", "descripcion", "precio", "stock", "categoria", "foto"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "campo-texto"}),
            "descripcion": forms.Textarea(attrs={"class": "campo-texto", "rows": 3}),
            "precio": forms.NumberInput(attrs={"class": "campo-texto", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "campo-texto"}),
            "categoria": forms.TextInput(attrs={"class": "campo-texto"}),
            "foto": forms.FileInput(attrs={"class": "campo-texto"}),
        }


class FormularioCuidadoPiel(forms.ModelForm):
    class Meta:
        model = CuidadoPiel
        fields = ["nombre", "descripcion", "precio", "stock", "categoria", "foto"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "campo-texto"}),
            "descripcion": forms.Textarea(attrs={"class": "campo-texto", "rows": 3}),
            "precio": forms.NumberInput(attrs={"class": "campo-texto", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "campo-texto"}),
            "categoria": forms.TextInput(attrs={"class": "campo-texto"}),
            "foto": forms.FileInput(attrs={"class": "campo-texto"}),
        }


class FormularioPerfume(forms.ModelForm):
    class Meta:
        model = Perfume
        fields = ["nombre", "descripcion", "precio", "stock", "categoria", "foto"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "campo-texto"}),
            "descripcion": forms.Textarea(attrs={"class": "campo-texto", "rows": 3}),
            "precio": forms.NumberInput(attrs={"class": "campo-texto", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "campo-texto"}),
            "categoria": forms.TextInput(attrs={"class": "campo-texto"}),
            "foto": forms.FileInput(attrs={"class": "campo-texto"}),
        }


class FormularioUsuarioAdmin(forms.ModelForm):
    nueva_contrasena = forms.CharField(
        label="Nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "campo-texto"}),
        help_text="Déjalo vacío para mantener la contraseña actual.",
    )

    class Meta:
        model = Usuario
        fields = [
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "correo_electronico",
            "direccion",
            "es_admin",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "campo-texto"}),
            "apellido": forms.TextInput(attrs={"class": "campo-texto"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"type": "date", "class": "campo-texto"}
            ),
            "correo_electronico": forms.EmailInput(attrs={"class": "campo-texto"}),
            "direccion": forms.Textarea(attrs={"class": "campo-texto", "rows": 3}),
            "es_admin": forms.CheckboxInput(attrs={"class": "casilla"}),
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva = self.cleaned_data.get("nueva_contrasena")
        if nueva:
            usuario.contrasena = make_password(nueva)
        if commit:
            usuario.save()
        return usuario


class FormularioPago(forms.Form):
    METODOS = (
        ("tarjeta", "Tarjeta"),
        ("paypal", "PayPal"),
    )
    metodo = forms.ChoiceField(
        choices=METODOS, widget=forms.Select(attrs={"class": "campo-texto"})
    )
    nombre_tarjeta = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "campo-texto"})
    )
    numero_tarjeta = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "campo-texto"})
    )
    mes_vencimiento = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "campo-texto"})
    )
    anio_vencimiento = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "campo-texto"})
    )
    cvv = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "campo-texto"})
    )
    correo_paypal = forms.EmailField(
        required=False, widget=forms.EmailInput(attrs={"class": "campo-texto"})
    )
    domicilio = forms.CharField(
        widget=forms.Textarea(attrs={"class": "campo-texto", "rows": 3})
    )