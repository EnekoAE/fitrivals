from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import Usuario, Ejercicio, Entrenamiento, Reto, EntrenamientoEjercicio
from .forms import RegistroUsuarioForm, LoginUsuarioForm, EntrenamientoForm


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


# Vistas de Entrenamientos + Historial de Retos
def lista_entrenamientos(request):
    entrenamientos = Entrenamiento.objects.select_related('usuario').order_by('-fecha')
    retos_completados = (
        Reto.objects.filter(Q(completado_por__isnull=False) | Q(intentos__isnull=False))
        .distinct()
        .prefetch_related('completado_por', 'intentos__usuario')
    )
    return render(request, 'entrenamientos/lista.html', {
        'entrenamientos': entrenamientos,
        'retos_completados': retos_completados,
    })


def detalle_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(Entrenamiento, pk=pk)
    return render(request, 'entrenamientos/detalle.html', {'entrenamiento': entrenamiento})


# Vistas Basadas en Clases para Retos Semanales (Opción 2 E4a)
class RetoListView(ListView):
    model = Reto
    template_name = 'retos/lista.html'
    context_object_name = 'retos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()

        context['retos_activos'] = Reto.objects.filter(
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).order_by('fecha_fin')

        context['retos_proximos'] = Reto.objects.filter(
            fecha_inicio__gt=hoy
        ).order_by('fecha_inicio')

        context['retos_pasados'] = Reto.objects.filter(
            fecha_fin__lt=hoy
        ).order_by('-fecha_fin')

        usuario_id = self.request.session.get('usuario_id')
        if usuario_id:
            context['retos_completados_ids'] = list(
                Reto.objects.filter(
                    Q(completado_por__id=usuario_id) | Q(intentos__usuario_id=usuario_id)
                ).values_list('id', flat=True).distinct()
            )
        else:
            context['retos_completados_ids'] = []

        return context


class RetoDetailView(DetailView):
    model = Reto
    template_name = 'retos/detalle.html'
    context_object_name = 'reto'


# FLUJO 1: Crear entrenamiento libre (NO es reto, NO suma puntos)
def crear_entrenamiento(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    usuario = get_object_or_404(Usuario, id=usuario_id)
    ejercicios = Ejercicio.objects.all()

    if request.method == 'POST':
        form = EntrenamientoForm(request.POST)
        if form.is_valid():
            entrenamiento = form.save(commit=False)
            entrenamiento.usuario = usuario
            entrenamiento.reto = None
            entrenamiento.fecha = date.today()
            entrenamiento.save()

            ejercicios_ids = request.POST.getlist('ejercicio')
            series_list = request.POST.getlist('series')
            reps_list = request.POST.getlist('repeticiones')
            pesos_list = request.POST.getlist('peso_kg')

            for ej_id, series, reps, peso in zip(ejercicios_ids, series_list, reps_list, pesos_list):
                if ej_id:
                    EntrenamientoEjercicio.objects.create(
                        entrenamiento=entrenamiento,
                        ejercicio_id=int(ej_id),
                        series=int(series or 3),
                        repeticiones=int(reps or 10),
                        peso_kg=float(peso or 0)
                    )

            return redirect('detalle_entrenamiento', pk=entrenamiento.pk)
    else:
        form = EntrenamientoForm()

    return render(request, 'entrenamientos/crear.html', {
        'form': form,
        'ejercicios': ejercicios
    })


# FLUJO 2: Completar un reto (CREA entrenamiento vinculado, SÍ suma puntos y soporta AJAX)
def completar_reto(request, pk):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'mensaje': 'Inicia sesión para completar retos.'})
        return redirect('login_usuario')

    usuario = get_object_or_404(Usuario, id=usuario_id)
    reto = get_object_or_404(Reto, pk=pk)

    if request.method == 'POST':
        duracion = int(request.POST.get('duracion_minutos', 30))
        notas = request.POST.get('notas', '')

        # 1. Creamos el entrenamiento asociado al reto
        entrenamiento = Entrenamiento.objects.create(
            usuario=usuario,
            reto=reto,
            fecha=date.today(),
            duracion_minutos=duracion,
            notas=notas or f"Reto superado: {reto.nombre}"
        )

        # 2. Guardamos las marcas de cada ejercicio del reto
        for ejercicio in reto.ejercicios.all():
            series = int(request.POST.get(f'series_{ejercicio.id}', 3))
            reps = int(request.POST.get(f'reps_{ejercicio.id}', 10))
            peso = float(request.POST.get(f'peso_{ejercicio.id}', 0))

            EntrenamientoEjercicio.objects.create(
                entrenamiento=entrenamiento,
                ejercicio=ejercicio,
                series=series,
                repeticiones=reps,
                peso_kg=peso
            )

        # 3. Marcamos completado y sumamos los puntos del reto al usuario
        reto.completado_por.add(usuario)
        usuario.puntos += reto.puntos_recompensa
        usuario.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'mensaje': f'¡Reto registrado! Has ganado +{reto.puntos_recompensa} puntos (Total: {usuario.puntos} pts).',
                'redirect_url': f'/entrenamientos/{entrenamiento.pk}/'
            })

        return redirect('detalle_entrenamiento', pk=entrenamiento.pk)

    return render(request, 'retos/completar.html', {'reto': reto})