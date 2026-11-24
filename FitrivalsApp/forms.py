from django import forms
from .models import Usuario
from .models import Entrenamiento


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
class EntrenamientoForm(forms.ModelForm):
    class Meta:
        model = Entrenamiento
        fields = ['duracion_minutos', 'notas']
        labels = {
            'duracion_minutos': 'Duración (minutos)',
            'notas': 'Notas de la sesión',
        }
        widgets = {
            'duracion_minutos': forms.NumberInput(attrs={'min': 1, 'placeholder': 'Ej: 45'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Sensaciones, rutina del día...'}),
        }