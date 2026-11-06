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