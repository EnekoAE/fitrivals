from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from .models import Usuario, Ejercicio, Entrenamiento, Reto
from .forms import RegistroUsuarioForm, LoginUsuarioForm


# Página Principal
def index(request):
    retos = Reto.objects.all()
    usuarios = Usuario.objects.order_by('-puntos')
    return render(request, 'index.html', {
        'retos': retos,
        'usuarios': usuarios,
    })


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
    usuarios = Usuario.objects.order_by('-puntos')
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


# Vistas Basadas en Clases para Retos Semanales (Opción 2 E4a)
class RetoListView(ListView):
    model = Reto
    template_name = 'retos/lista.html'
    context_object_name = 'retos'


class RetoDetailView(DetailView):
    model = Reto
    template_name = 'retos/detalle.html'
    context_object_name = 'reto'


# Vista AJAX para completar reto semanal y sumar puntos (Opción 1 E4a)
def completar_reto(request, pk):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'ok': False, 'mensaje': 'Inicia sesión para sumar puntos.'})

    usuario = get_object_or_404(Usuario, id=usuario_id)
    reto = get_object_or_404(Reto, id=pk)

    if reto.completado_por.filter(id=usuario.id).exists():
        return JsonResponse({'ok': False, 'mensaje': 'Ya habías completado este reto.'})

    reto.completado_por.add(usuario)
    usuario.puntos += reto.puntos_recompensa
    usuario.save()

    return JsonResponse({
        'ok': True,
        'mensaje': f'¡Genial! Has ganado +{reto.puntos_recompensa} puntos.',
        'puntos_totales': usuario.puntos,
    })