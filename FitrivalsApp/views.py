from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from .models import Usuario, Ejercicio, Entrenamiento, Reto, EntrenamientoEjercicio
from .forms import RegistroUsuarioForm, LoginUsuarioForm, EntrenamientoForm



def _entero(valor, defecto, minimo=1, maximo=10000):
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return defecto
    return max(minimo, min(n, maximo))


def _decimal(valor, defecto=Decimal('0'), maximo=Decimal('999.99')):
    try:
        d = Decimal(str(valor).replace(',', '.'))
    except (InvalidOperation, TypeError, ValueError):
        return defecto
    return max(Decimal('0'), min(d, maximo))


def _es_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


# Página Principal
def index(request):
    retos = Reto.objects.all()
    usuarios = Usuario.objects.order_by('-puntos')
    usuarios_amigos = None

    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        yo = Usuario.objects.filter(pk=usuario_id).first()
        if yo:
            ids_circulo = list(yo.amigos.values_list('id', flat=True)) + [yo.id]
            usuarios_amigos = Usuario.objects.filter(id__in=ids_circulo).order_by('-puntos')

    return render(request, 'index.html', {
        'retos': retos,
        'usuarios': usuarios,
        'usuarios_amigos': usuarios_amigos,
    })

@require_POST
def toggle_amigo(request, pk):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)
    otro = get_object_or_404(Usuario, pk=pk)

    if yo.pk != otro.pk:
        if yo.amigos.filter(pk=otro.pk).exists():
            yo.amigos.remove(otro)
            messages.info(request, f'Has eliminado a {otro.nombre} de tu círculo.')
        else:
            yo.amigos.add(otro)
            messages.success(request, f'¡{otro.nombre} añadido a tu círculo de amigos!')

    return redirect('detalle_usuario', pk=otro.pk)

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

@require_POST
def logout_usuario(request):
    request.session.flush()
    return redirect('index')


# Vistas de Usuarios
def lista_usuarios(request):
    usuarios = Usuario.objects.order_by('-puntos')
    return render(request, 'usuarios/lista.html', {'usuarios': usuarios})


def detalle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    entrenamientos = usuario.entrenamientos.select_related('reto').order_by('-fecha')
    es_amigo = False

    usuario_id = request.session.get('usuario_id')
    if usuario_id and usuario_id != usuario.pk:
        yo = Usuario.objects.filter(pk=usuario_id).first()
        if yo:
            es_amigo = yo.amigos.filter(pk=usuario.pk).exists()

    return render(request, 'usuarios/detalle.html', {
        'usuario': usuario,
        'entrenamientos': entrenamientos,
        'es_amigo': es_amigo,
    })


# Vistas de Ejercicios
def lista_ejercicios(request):
    ejercicios = Ejercicio.objects.all()
    return render(request, 'ejercicios/lista.html', {'ejercicios': ejercicios})


def detalle_ejercicio(request, pk):
    ejercicio = get_object_or_404(Ejercicio, pk=pk)
    return render(request, 'ejercicios/detalle.html', {'ejercicio': ejercicio})


# Vistas de Entrenamientos + Historial de Retos
def lista_entrenamientos(request):
    entrenamientos = Entrenamiento.objects.select_related('usuario', 'reto').order_by('-fecha')
    solo_amigos = request.GET.get('filtro') == 'amigos'
    usuario_id = request.session.get('usuario_id')

    if solo_amigos and usuario_id:
        yo = Usuario.objects.filter(pk=usuario_id).first()
        if yo:
            ids_circulo = list(yo.amigos.values_list('id', flat=True)) + [yo.id]
            entrenamientos = entrenamientos.filter(usuario_id__in=ids_circulo)

    retos_completados = (
        Reto.objects.filter(Q(completado_por__isnull=False) | Q(intentos__isnull=False))
        .distinct()
        .prefetch_related('completado_por', 'intentos__usuario')
    )
    return render(request, 'entrenamientos/lista.html', {
        'entrenamientos': entrenamientos,
        'retos_completados': retos_completados,
        'solo_amigos': solo_amigos,
    })


def detalle_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(
        Entrenamiento.objects.select_related('usuario', 'reto'), pk=pk
    )
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
        ).prefetch_related('ejercicios').order_by('fecha_fin')

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
    queryset = Reto.objects.prefetch_related('ejercicios', 'intentos__usuario')
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
            entrenamiento.fecha = timezone.localdate()
            entrenamiento.save()

            ejercicios_ids = request.POST.getlist('ejercicio')
            series_list = request.POST.getlist('series')
            reps_list = request.POST.getlist('repeticiones')
            pesos_list = request.POST.getlist('peso_kg')
            ids_validos = set(Ejercicio.objects.values_list('id', flat=True))

            for ej_id, series, reps, peso in zip(ejercicios_ids, series_list, reps_list, pesos_list):
                if ej_id.isdigit() and int(ej_id) in ids_validos:
                    EntrenamientoEjercicio.objects.create(
                        entrenamiento=entrenamiento,
                        ejercicio_id=int(ej_id),
                        series=_entero(series, 3),
                        repeticiones=_entero(reps, 10),
                        peso_kg=_decimal(peso),
                    )

            return redirect('detalle_entrenamiento', pk=entrenamiento.pk)
    else:
        form = EntrenamientoForm()

    return render(request, 'entrenamientos/crear.html', {
        'form': form,
        'ejercicios': ejercicios,
    })


# FLUJO 2: Completar un reto (CREA entrenamiento vinculado, SÍ suma puntos y soporta AJAX)
def _rechazar(request, reto, mensaje, status=400):
    if _es_ajax(request):
        return JsonResponse({'ok': False, 'mensaje': mensaje}, status=status)
    messages.error(request, mensaje)
    return redirect('detalle_reto', pk=reto.pk)


def completar_reto(request, pk):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        if _es_ajax(request):
            return JsonResponse({'ok': False, 'mensaje': 'Inicia sesión para completar retos.'}, status=401)
        return redirect('login_usuario')

    usuario = get_object_or_404(Usuario, id=usuario_id)
    reto = get_object_or_404(Reto, pk=pk)

    if reto.estado_semana != 'ACTIVO':
        return _rechazar(request, reto, 'Este reto no está activo esta semana.')
    if Entrenamiento.objects.filter(usuario=usuario, reto=reto).exists() \
            or reto.completado_por.filter(pk=usuario.pk).exists():
        return _rechazar(request, reto, 'Ya has completado este reto.')

    if request.method == 'POST':
        duracion = _entero(request.POST.get('duracion_minutos'), 30)
        notas = request.POST.get('notas', '')[:2000]

        with transaction.atomic():
            entrenamiento = Entrenamiento.objects.create(
                usuario=usuario,
                reto=reto,
                fecha=timezone.localdate(),
                duracion_minutos=duracion,
                notas=notas or f"Reto superado: {reto.nombre}",
            )

            for ejercicio in reto.ejercicios.all():
                EntrenamientoEjercicio.objects.create(
                    entrenamiento=entrenamiento,
                    ejercicio=ejercicio,
                    series=_entero(request.POST.get(f'series_{ejercicio.id}'), 3),
                    repeticiones=_entero(request.POST.get(f'reps_{ejercicio.id}'), 10),
                    peso_kg=_decimal(request.POST.get(f'peso_{ejercicio.id}')),
                )

            reto.completado_por.add(usuario)
            Usuario.objects.filter(pk=usuario.pk).update(puntos=F('puntos') + reto.puntos_recompensa)

        usuario.refresh_from_db()
        if _es_ajax(request):
            return JsonResponse({
                'ok': True,
                'mensaje': f'¡Reto registrado! Has ganado +{reto.puntos_recompensa} puntos (Total: {usuario.puntos} pts).',
                'redirect_url': redirect('detalle_entrenamiento', pk=entrenamiento.pk).url,
            })

        messages.success(request, f'¡Reto registrado! +{reto.puntos_recompensa} puntos.')
        return redirect('detalle_entrenamiento', pk=entrenamiento.pk)

    return render(request, 'retos/completar.html', {'reto': reto})