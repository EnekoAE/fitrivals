from django import forms
from .models import Usuario


class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Crea una contraseña',
            'required': True,
        })
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'password']
        labels = {
            'nombre': 'Nombre de usuario',
            'email': 'Correo electrónico',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. jonzaldivar',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'tuemail@ejemplo.com',
                'required': True,
            }),
        }


class LoginUsuarioForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={
            'placeholder': 'Introduce tu nombre de usuario',
            'required': True,
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Introduce tu contraseña',
            'required': True,
        })
    )