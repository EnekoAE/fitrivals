from django.shortcuts import render
from .models import Usuario, Ejercicio, Entrenamiento, Reto


def index(request):
    contexto = {
        'num_usuarios': Usuario.objects.count(),
        'num_ejercicios': Ejercicio.objects.count(),
        'num_entrenamientos': Entrenamiento.objects.count(),
        'num_retos': Reto.objects.count(),
    }
    return render(request, 'index.html', contexto)