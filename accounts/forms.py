import re
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Store, User


class RegistrationForm(forms.Form):
    full_name = forms.CharField(label="Nombre completo", max_length=150, widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"autocomplete": "off"}))
    store = forms.ModelChoiceField(queryset=Store.objects.all(), label="Tienda asignada")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_password1(self):
        value = self.cleaned_data["password1"]
        if len(value) < 8 or not re.search(r"[A-Z]", value) or not re.search(r"\d", value) or not re.search(r"[^\w\s]", value):
            raise ValidationError("Usa al menos 8 caracteres, una mayúscula, un número y un símbolo.")
        validate_password(value)
        return value

    def clean(self):
        data = super().clean()
        if data.get("password1") and data.get("password2") and data["password1"] != data["password2"]:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return data


class TeamEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "role", "store", "is_active")
        labels = {"full_name": "Nombre completo", "role": "Rol", "store": "Tienda asignada", "is_active": "Cuenta activa"}


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ("name", "location")
        labels = {"name": "Nombre de la tienda", "location": "Ubicación"}


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("avatar_url",)
        labels = {"avatar_url": "Enlace de la foto de perfil"}
        widgets = {"avatar_url": forms.URLInput(attrs={
            "placeholder": "https://ejemplo.com/mi-foto.jpg", "autocomplete": "url",
        })}

    def clean_avatar_url(self):
        url = self.cleaned_data["avatar_url"].strip()
        if url and not url.lower().startswith("https://"):
            raise ValidationError("Usa un enlace HTTPS directo a la imagen.")
        return url
