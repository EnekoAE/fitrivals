from decimal import Decimal

from django.contrib.auth.hashers import identify_hasher, make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from FitrivalsApp.models import (
    Circulo, Ejercicio, Entrenamiento, EntrenamientoEjercicio,
    InvitacionCirculo, Reto, Usuario, fin_semana, inicio_semana,
)

PASSWORD_DEMO = 'Fitrivals1234'

EJERCICIOS = [
    ('Sentadilla', 'PIERNA', 'FACIL', 'Flexión de rodillas y cadera con la espalda recta hasta bajar los muslos paralelos al suelo.'),
    ('Sentadilla bulgara', 'PIERNA', 'INTERMEDIO', 'Sentadilla a una pierna con el pie trasero apoyado en un banco.'),
    ('Dominada', 'ESPALDA', 'INTERMEDIO', 'Elevar el cuerpo colgado de una barra hasta pasar la barbilla por encima.'),
    ('Jalón al pecho', 'ESPALDA', 'FACIL', 'Tracción de la polea alta hacia el pecho para trabajar el dorsal ancho.'),
    ('Remo en V', 'ESPALDA', 'FACIL', 'Remo sentado con agarre en V para trabajar la zona media de la espalda.'),
    ('Remo en T', 'ESPALDA', 'INTERMEDIO', 'Remo con barra en T para trabajar dorsal y romboides.'),
    ('Remo maquina', 'ESPALDA', 'FACIL', 'Remo guiado en máquina con el pecho apoyado.'),
    ('Press de Banca', 'PECHO', 'INTERMEDIO', 'Empuje de la barra desde el pecho tumbado en un banco plano.'),
    ('Press inclinado', 'PECHO', 'INTERMEDIO', 'Press en banco inclinado que carga la parte alta del pecho.'),
    ('Aperturas en peck deck', 'PECHO', 'FACIL', 'Aperturas en máquina para aislar el pectoral.'),
    ('Press militar', 'HOMBROS', 'AVANZADO', 'Empuje vertical de la barra por encima de la cabeza.'),
    ('Elevaciones laterales', 'HOMBROS', 'FACIL', 'Elevar mancuernas lateralmente hasta la altura del hombro.'),
    ('Reverse flu', 'HOMBROS', 'FACIL', 'Aperturas inversas para trabajar el deltoides posterior.'),
    ('Curl de biceps', 'BRAZOS', 'FACIL', 'Flexión de codos con mancuernas para trabajar el bíceps.'),
    ('Curl martillo', 'BRAZOS', 'FACIL', 'Curl con agarre neutro que trabaja bíceps y braquial.'),
    ('Curl bayesian', 'BRAZOS', 'INTERMEDIO', 'Curl en polea con el brazo por detrás del cuerpo para estirar el bíceps.'),
    ('Press frances', 'BRAZOS', 'AVANZADO', 'Extensión de codos tumbado con barra para trabajar el tríceps.'),
    ('Extension de triceps en polea alta', 'BRAZOS', 'FACIL', 'Extensión de codos en polea alta con cuerda o barra.'),
    ('Extension de triceps en polea baja', 'BRAZOS', 'INTERMEDIO', 'Extensión de tríceps por encima de la cabeza con polea baja.'),
    ('Plancha plana', 'CORE', 'FACIL', 'Mantener el cuerpo alineado apoyado en antebrazos y puntas de los pies.'),
]

USUARIOS = [
    ('Jon Z', 'jon.z@fitrivals.test'),
    ('Dvid Zhu', 'dvid.zhu@fitrivals.test'),
    ('AL', 'al@fitrivals.test'),
    ('EnekoEA', 'enekoea@fitrivals.test'),
    ('Ane', 'ane@fitrivals.test'),
]

RETOS = [
    ('Full body al fallo', 'Circuito de cuerpo entero hasta el fallo muscular.', 10,
     ['Sentadilla', 'Dominada', 'Press de Banca', 'Plancha plana']),
    ('Press banca 100x8', 'Levanta 100 kg durante 8 repeticiones en press de banca.', 300,
     ['Press de Banca', 'Press inclinado']),
    ('Sentadilla 100', 'Haz 100 sentadillas en una sola sesión.', 100,
     ['Sentadilla', 'Sentadilla bulgara']),
    ('Disciplina navy seal', 'Rutina de resistencia: fuerza y core sin excusas.', 1000,
     ['Dominada', 'Press militar', 'Plancha plana', 'Remo en T']),
    ('Recompensa diaria', 'Entrena hoy y llévate unos puntos extra.', 3,
     ['Curl de biceps', 'Elevaciones laterales']),
    ('Press frances 30', 'Treinta repeticiones de press francés con buena técnica.', 80,
     ['Press frances', 'Curl martillo']),
]


class Command(BaseCommand):
    help = 'Carga el juego de ensayo de Fit Rivals'

    @transaction.atomic
    def handle(self, *args, **options):
        ejercicios = {}
        for nombre, grupo, dificultad, desc in EJERCICIOS:
            ej, _ = Ejercicio.objects.get_or_create(
                nombre=nombre,
                defaults={'grupo_muscular': grupo, 'dificultad': dificultad, 'descripcion': desc},
            )
            if not ej.descripcion:
                ej.descripcion = desc
                ej.save(update_fields=['descripcion'])
            ejercicios[nombre] = ej

        for nombre, email in USUARIOS:
            Usuario.objects.get_or_create(
                nombre=nombre,
                defaults={'email': email, 'password': make_password(PASSWORD_DEMO)},
            )

        rehasheadas = 0
        for u in Usuario.objects.all():
            try:
                identify_hasher(u.password)
            except ValueError:
                u.password = make_password(u.password or PASSWORD_DEMO)
                u.save(update_fields=['password'])
                rehasheadas += 1

        for nombre, desc, puntos, ejs in RETOS:
            reto, _ = Reto.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc, 'puntos_recompensa': puntos},
            )
            reto.fecha_inicio = inicio_semana()
            reto.fecha_fin = fin_semana()
            reto.save(update_fields=['fecha_inicio', 'fecha_fin'])
            if not reto.ejercicios.exists():
                reto.ejercicios.set([ejercicios[e] for e in ejs])

        usuarios = list(Usuario.objects.order_by('id'))

        if not Circulo.objects.exists() and len(usuarios) >= 4:
            circulo = Circulo.objects.create(
                nombre='Gimnasio Deusto',
                descripcion='Círculo de ejemplo para comparar marcas semanales.',
                anfitrion=usuarios[0],
            )
            circulo.miembros.set(usuarios[:3])
            InvitacionCirculo.objects.create(circulo=circulo, invitado=usuarios[0], estado='ACEPTADA')
            InvitacionCirculo.objects.create(circulo=circulo, invitado=usuarios[3], estado='PENDIENTE')
            if len(usuarios) > 4:
                InvitacionCirculo.objects.create(circulo=circulo, invitado=usuarios[4], estado='RECHAZADA')

        if not Entrenamiento.objects.exists():
            for usuario in usuarios[:3]:
                ent = Entrenamiento.objects.create(
                    usuario=usuario,
                    fecha=inicio_semana(),
                    duracion_minutos=45,
                    notas='Sesión de ejemplo',
                )
                for ej in list(ejercicios.values())[:3]:
                    EntrenamientoEjercicio.objects.create(
                        entrenamiento=ent,
                        ejercicio=ej,
                        series=3,
                        repeticiones=10,
                        peso_kg=Decimal('20'),
                    )

        self.stdout.write(self.style.SUCCESS(
            f'{Ejercicio.objects.count()} ejercicios, {Usuario.objects.count()} usuarios, '
            f'{Circulo.objects.count()} círculos, {InvitacionCirculo.objects.count()} invitaciones, '
            f'{Reto.objects.count()} retos, {Entrenamiento.objects.count()} entrenamientos, '
            f'{rehasheadas} contraseñas rehasheadas'
        ))