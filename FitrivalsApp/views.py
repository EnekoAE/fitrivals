from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password, check_password
from .models import Usuario, Ejercicio, Entrenamiento, Reto
from .forms import RegistroUsuarioForm, LoginUsuarioForm


# Página Principal
def index(request):
    return render(request, 'index.html')


# Portal de Usuarios: Registro, Login y Logout
def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.password = make_password(form.cleaned_data['password'])
            usuario.save()
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nombre'] = usuario.nombre
            return redirect('index')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def login_usuario(request):
    error = None
    if request.method == 'POST':
        form = LoginUsuarioForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            password = form.cleaned_data['password']
            usuario = Usuario.objects.filter(nombre=nombre).first()
            if usuario and check_password(password, usuario.password):
                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.nombre
                return redirect('index')
            else:
                error = 'Nombre de usuario o contraseña incorrectos.'
    else:
        form = LoginUsuarioForm()
    return render(request, 'usuarios/login.html', {'form': form, 'error': error})


def logout_usuario(request):
    request.session.flush()
    return redirect('index')


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