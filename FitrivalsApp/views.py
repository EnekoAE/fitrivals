from django.shortcuts import render, get_object_or_404
from .models import Usuario, Ejercicio, Entrenamiento, Reto

# Página Principal
def index(request):
    return render(request, 'index.html')

# Vistas de Usuarios
def lista_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios})

def detalle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    return render(request, 'usuarios/detalle.html', {'usuario': usuario})

# Vistas de Ejercicios
def lista_ejercicios(request):
    ejercicios = Ejercicio.objects.all()
    return render(request, 'ejercicios/lista.html', {'ejercicios': ejercicios})

def detalle_ejercicio(request, pk):
    ejercicio = get_object_or_404(Ejercicio, pk=pk)
    return render(request, 'ejercicios/detalle.html', {'ejercicio': ejercicio})

# Vistas de Entrenamientos
def lista_entrenamientos(request):
    entrenamientos = Entrenamiento.objects.all()
    return render(request, 'entrenamientos/lista.html', {'entrenamientos': entrenamientos})

def detalle_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(Entrenamiento, pk=pk)
    return render(request, 'entrenamientos/detalle.html', {'entrenamiento': entrenamiento})

# Vistas de Retos
def lista_retos(request):
    retos = Reto.objects.all()
    return render(request, 'retos/lista.html', {'retos': retos})

def detalle_reto(request, pk):
    reto = get_object_or_404(Reto, pk=pk)
    return render(request, 'retos/detalle.html', {'reto': reto})