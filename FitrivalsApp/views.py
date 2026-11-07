from django.shortcuts import render, get_object_or_404
from .models import Usuario, Ejercicio, Entrenamiento, Reto


def index(request):
    contexto = {
        'num_usuarios': Usuario.objects.count(),
        'num_ejercicios': Ejercicio.objects.count(),
        'num_entrenamientos': Entrenamiento.objects.count(),
        'num_retos': Reto.objects.count(),
    }
    return render(request, 'index.html', contexto)

def lista_usuarios(request):
    usuarios = Usuario.objects.order_by('-puntos')
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios})

def detalle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    entrenamientos = usuario.entrenamientos.order_by('-fecha')
    retos = usuario.retos.all()
    return render(request, 'usuarios/detalle.html', {
        'usuario': usuario,
        'entrenamientos': entrenamientos,
        'retos': retos,
    })



def lista_entrenamientos(request):
    entrenamientos = Entrenamiento.objects.select_related('usuario').order_by('-fecha')
    return render(request, 'entrenamientos/lista.html', {'entrenamientos': entrenamientos})

def detalle_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(Entrenamiento, pk=pk)
    lineas = entrenamiento.entrenamientoejercicio_set.select_related('ejercicio')
    return render(request, 'entrenamientos/detalle.html', {
        'entrenamiento': entrenamiento,
        'lineas': lineas,
    })

def lista_ejercicios(request):
    ejercicios = Ejercicio.objects.order_by('nombre')
    return render(request, 'ejercicios/lista.html', {'ejercicios': ejercicios})

def detalle_ejercicio(request, pk):
    ejercicio = get_object_or_404(Ejercicio, pk=pk)
    entrenamientos = ejercicio.entrenamiento_set.select_related('usuario').order_by('-fecha')
    return render(request, 'ejercicios/detalle.html', {
        'ejercicio': ejercicio,
        'entrenamientos': entrenamientos,
    })