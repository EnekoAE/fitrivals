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
from .models import (
    Usuario, Circulo, InvitacionCirculo,
    Ejercicio, Entrenamiento, Reto, EntrenamientoEjercicio
)
from .forms import RegistroUsuarioForm, LoginUsuarioForm, EntrenamientoForm, CirculoForm


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


def _obtener_circulo_activo(request, mis_circulos):
    circulo_id = request.GET.get('circulo')
    if circulo_id and circulo_id.isdigit():
        seleccionado = mis_circulos.filter(pk=int(circulo_id)).first()
        if seleccionado:
            return seleccionado
    return mis_circulos.first()


# Página Principal (Sin clasificación global: botones para cambiar entre tus círculos)
def index(request):
    retos = Reto.objects.all()
    mis_circulos = Circulo.objects.none()
    circulo_activo = None
    ranking_circulo = []
    entrenamientos_circulo = []
    invitaciones_pendientes = []

    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        yo = Usuario.objects.filter(pk=usuario_id).first()
        if yo:
            mis_circulos = yo.circulos.all().order_by('nombre')
            circulo_activo = _obtener_circulo_activo(request, mis_circulos)
            invitaciones_pendientes = InvitacionCirculo.objects.filter(
                invitado=yo, estado='PENDIENTE'
            ).select_related('circulo', 'circulo__anfitrion')

            if circulo_activo:
                ranking_circulo = circulo_activo.miembros.order_by('-puntos')
                entrenamientos_circulo = (
                    Entrenamiento.objects.filter(
                        usuario__in=circulo_activo.miembros.all(),
                        reto__isnull=True
                    )
                    .select_related('usuario')
                    .prefetch_related('entrenamientoejercicio_set__ejercicio')
                    .order_by('-fecha')[:6]
                )

    return render(request, 'index.html', {
        'retos': retos,
        'mis_circulos': mis_circulos,
        'circulo_activo': circulo_activo,
        'ranking_circulo': ranking_circulo,
        'entrenamientos_circulo': entrenamientos_circulo,
        'invitaciones_pendientes': invitaciones_pendientes,
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


@require_POST
def logout_usuario(request):
    request.session.flush()
    return redirect('index')


# Directorio de Atletas (buscador para invitar gente a tus círculos, sin ranking global)
def lista_usuarios(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)
    query = request.GET.get('q', '').strip()

    atletas = Usuario.objects.exclude(pk=yo.pk).order_by('nombre')
    if query:
        atletas = atletas.filter(nombre__icontains=query)

    mis_circulos_anfitrion = Circulo.objects.filter(anfitrion=yo).order_by('nombre')

    return render(request, 'usuarios/lista.html', {
        'atletas': atletas,
        'query': query,
        'mis_circulos_anfitrion': mis_circulos_anfitrion,
    })


def detalle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario_id = request.session.get('usuario_id')
    es_mi_perfil = (usuario_id == usuario.pk)
    comparten_circulo = False

    mis_circulos_usuario = usuario.circulos.all().order_by('nombre')
    invitaciones_pendientes = []
    circulos_para_invitar = []
    entrenamientos = []

    if usuario_id:
        yo = Usuario.objects.filter(pk=usuario_id).first()
        if yo:
            if es_mi_perfil:
                invitaciones_pendientes = InvitacionCirculo.objects.filter(
                    invitado=yo, estado='PENDIENTE'
                ).select_related('circulo', 'circulo__anfitrion')
                entrenamientos = usuario.entrenamientos.filter(reto__isnull=True).order_by('-fecha')
            else:
                comparten_circulo = Circulo.objects.filter(miembros=yo).filter(miembros=usuario).exists()
                if comparten_circulo:
                    entrenamientos = usuario.entrenamientos.filter(reto__isnull=True).order_by('-fecha')

                circulos_para_invitar = (
                    Circulo.objects.filter(anfitrion=yo)
                    .exclude(miembros=usuario)
                    .order_by('nombre')
                )

    return render(request, 'usuarios/detalle.html', {
        'usuario': usuario,
        'es_mi_perfil': es_mi_perfil,
        'comparten_circulo': comparten_circulo,
        'mis_circulos_usuario': mis_circulos_usuario,
        'invitaciones_pendientes': invitaciones_pendientes,
        'circulos_para_invitar': circulos_para_invitar,
        'entrenamientos': entrenamientos,
    })


# Gestión de Círculos e Invitaciones
def lista_circulos(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)
    mis_circulos = yo.circulos.all().order_by('nombre')
    invitaciones_pendientes = InvitacionCirculo.objects.filter(
        invitado=yo, estado='PENDIENTE'
    ).select_related('circulo', 'circulo__anfitrion')

    return render(request, 'circulos/lista.html', {
        'mis_circulos': mis_circulos,
        'invitaciones_pendientes': invitaciones_pendientes,
    })


def crear_circulo(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        form = CirculoForm(request.POST, usuario_actual=yo)
        if form.is_valid():
            circulo = form.save(commit=False)
            circulo.anfitrion = yo
            circulo.save()
            circulo.miembros.add(yo)

            invitados = form.cleaned_data.get('invitados')
            if invitados:
                for atleta in invitados:
                    InvitacionCirculo.objects.get_or_create(
                        circulo=circulo,
                        invitado=atleta,
                        defaults={'estado': 'PENDIENTE'}
                    )

            messages.success(request, f'¡Círculo "{circulo.nombre}" creado! Se han enviado las invitaciones.')
            return redirect('detalle_circulo', pk=circulo.pk)
    else:
        form = CirculoForm(usuario_actual=yo)

    return render(request, 'circulos/crear.html', {'form': form})


def detalle_circulo(request, pk):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)
    circulo = get_object_or_404(Circulo, pk=pk)

    if not circulo.miembros.filter(pk=yo.pk).exists():
        messages.error(request, 'No perteneces a este círculo.')
        return redirect('lista_circulos')

    ranking = circulo.miembros.order_by('-puntos')
    entrenamientos = (
        Entrenamiento.objects.filter(usuario__in=circulo.miembros.all(), reto__isnull=True)
        .select_related('usuario')
        .prefetch_related('entrenamientoejercicio_set__ejercicio')
        .order_by('-fecha')
    )

    es_anfitrion = (circulo.anfitrion_id == yo.pk)
    atletas_disponibles = []
    invitaciones_enviadas = []

    if es_anfitrion:
        ids_miembros = list(circulo.miembros.values_list('id', flat=True))
        ids_pendientes = list(
            circulo.invitaciones.filter(estado='PENDIENTE').values_list('invitado_id', flat=True)
        )
        atletas_disponibles = Usuario.objects.exclude(id__in=ids_miembros + ids_pendientes).order_by('nombre')
        invitaciones_enviadas = circulo.invitaciones.filter(estado='PENDIENTE').select_related('invitado')

    return render(request, 'circulos/detalle.html', {
        'circulo': circulo,
        'ranking': ranking,
        'entrenamientos': entrenamientos,
        'es_anfitrion': es_anfitrion,
        'atletas_disponibles': atletas_disponibles,
        'invitaciones_enviadas': invitaciones_enviadas,
    })


@require_POST
def invitar_circulo(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)
    circulo_id = request.POST.get('circulo_id')
    invitado_id = request.POST.get('invitado_id')
    next_url = request.POST.get('next')

    circulo = get_object_or_404(Circulo, pk=circulo_id, anfitrion=yo)
    atleta = get_object_or_404(Usuario, pk=invitado_id)

    if circulo.miembros.filter(pk=atleta.pk).exists():
        messages.info(request, f'{atleta.nombre} ya forma parte de "{circulo.nombre}".')
    else:
        invitacion, creada = InvitacionCirculo.objects.get_or_create(
            circulo=circulo,
            invitado=atleta,
            defaults={'estado': 'PENDIENTE'}
        )
        if not creada:
            if invitacion.estado == 'PENDIENTE':
                messages.info(request, f'Ya hay una solicitud pendiente para {atleta.nombre} en "{circulo.nombre}".')
            else:
                invitacion.estado = 'PENDIENTE'
                invitacion.save()
                messages.success(request, f'Solicitud reenviada a {atleta.nombre} para unirse a "{circulo.nombre}".')
        else:
            messages.success(request, f'Solicitud enviada a {atleta.nombre} para unirse a "{circulo.nombre}".')

    if next_url:
        return redirect(next_url)
    return redirect('detalle_circulo', pk=circulo.pk)


@require_POST
def responder_invitacion(request, pk):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    yo = get_object_or_404(Usuario, pk=usuario_id)
    invitacion = get_object_or_404(InvitacionCirculo, pk=pk, invitado=yo, estado='PENDIENTE')
    accion = request.POST.get('accion')

    if accion == 'aceptar':
        invitacion.estado = 'ACEPTADA'
        invitacion.save()
        invitacion.circulo.miembros.add(yo)
        messages.success(request, f'¡Te has unido al círculo "{invitacion.circulo.nombre}"!')
        return redirect('detalle_circulo', pk=invitacion.circulo.pk)
    elif accion == 'rechazar':
        invitacion.estado = 'RECHAZADA'
        invitacion.save()
        messages.info(request, f'Has rechazado la invitación a "{invitacion.circulo.nombre}".')

    return redirect('lista_circulos')


# Vistas de Ejercicios
def lista_ejercicios(request):
    ejercicios = Ejercicio.objects.all()
    return render(request, 'ejercicios/lista.html', {'ejercicios': ejercicios})


def detalle_ejercicio(request, pk):
    ejercicio = get_object_or_404(Ejercicio, pk=pk)
    return render(request, 'ejercicios/detalle.html', {'ejercicio': ejercicio})


# Redirige cualquier acceso antiguo de entrenamientos a la pestaña de Círculos
def lista_entrenamientos(request):
    return redirect('lista_circulos')


def detalle_entrenamiento(request, pk):
    entrenamiento = get_object_or_404(
        Entrenamiento.objects.select_related('usuario', 'reto'), pk=pk
    )
    return render(request, 'entrenamientos/detalle.html', {'entrenamiento': entrenamiento})


# Vistas Basadas en Clases para Retos Semanales (1 reto activo por semana)
class RetoListView(ListView):
    model = Reto
    template_name = 'retos/lista.html'
    context_object_name = 'retos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()

        activos = Reto.objects.filter(
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).prefetch_related('ejercicios').order_by('fecha_inicio')

        context['reto_activo'] = activos.first()
        context['retos_activos'] = activos

        context['retos_proximos'] = Reto.objects.filter(
            fecha_inicio__gt=hoy
        ).order_by('fecha_inicio')

        context['retos_pasados'] = Reto.objects.filter(
            fecha_fin__lt=hoy
        ).order_by('-fecha_fin')

        usuario_id = self.request.session.get('usuario_id')
        if usuario_id:
            context['retos_completados_ids'] = list(
                Reto.objects.filter(completado_por__id=usuario_id)
                .values_list('id', flat=True).distinct()
            )
        else:
            context['retos_completados_ids'] = []

        return context


class RetoDetailView(DetailView):
    model = Reto
    queryset = Reto.objects.prefetch_related('ejercicios', 'completado_por')
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


# FLUJO 2: Completar un reto (NO crea entrenamiento, SÍ suma puntos y soporta AJAX)
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
    if reto.completado_por.filter(pk=usuario.pk).exists():
        return _rechazar(request, reto, 'Ya has completado este reto.')

    if request.method == 'POST':
        with transaction.atomic():
            reto.completado_por.add(usuario)
            Usuario.objects.filter(pk=usuario.pk).update(puntos=F('puntos') + reto.puntos_recompensa)

        usuario.refresh_from_db()
        if _es_ajax(request):
            return JsonResponse({
                'ok': True,
                'mensaje': f'¡Reto completado! Has ganado +{reto.puntos_recompensa} puntos (Total: {usuario.puntos} pts).',
                'redirect_url': redirect('detalle_reto', pk=reto.pk).url,
            })

        messages.success(request, f'¡Reto completado! +{reto.puntos_recompensa} puntos.')
        return redirect('detalle_reto', pk=reto.pk)

    return render(request, 'retos/completar.html', {'reto': reto})  