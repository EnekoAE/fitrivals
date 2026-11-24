import datetime
from django.db import models
from django.utils import timezone


class Usuario(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    fecha_alta = models.DateField(auto_now_add=True)
    puntos = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} ({self.puntos} pts)"


class Ejercicio(models.Model):
    GRUPOS_MUSCULARES = [
        ('PECHO', 'Pecho'),
        ('ESPALDA', 'Espalda'),
        ('PIERNA', 'Pierna'),
        ('BRAZOS', 'Brazos'),
        ('HOMBROS', 'Hombros'),
        ('CORE', 'Core'),
    ]

    DIFICULTAD_CHOICES = [
        ('FACIL', 'Fácil'),
        ('INTERMEDIO', 'Intermedio'),
        ('AVANZADO', 'Avanzado'),
    ]

    nombre = models.CharField(max_length=100)
    grupo_muscular = models.CharField(max_length=20, choices=GRUPOS_MUSCULARES)
    dificultad = models.CharField(max_length=20, choices=DIFICULTAD_CHOICES)

    def __str__(self):
        return f"{self.nombre} ({self.get_grupo_muscular_display()})"


class Entrenamiento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='entrenamientos')
    fecha = models.DateField()
    duracion_minutos = models.PositiveIntegerField(help_text="Duración en minutos")
    notas = models.TextField(blank=True, null=True)
    ejercicios = models.ManyToManyField(Ejercicio, through='EntrenamientoEjercicio')

    def __str__(self):
        return f"Entrenamiento de {self.usuario.nombre} - {self.fecha}"


class EntrenamientoEjercicio(models.Model):
    entrenamiento = models.ForeignKey(Entrenamiento, on_delete=models.CASCADE)
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE)
    series = models.PositiveIntegerField(default=3)
    repeticiones = models.PositiveIntegerField(default=10)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, help_text="Peso en kg")

    def __str__(self):
        return f"{self.ejercicio.nombre} en {self.entrenamiento}"


class Reto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    puntos_recompensa = models.IntegerField(default=100)
    fecha_inicio = models.DateField(default=datetime.date(2026, 11, 23))
    fecha_fin = models.DateField(default=datetime.date(2026, 11, 30))
    ejercicios = models.ManyToManyField(Ejercicio, related_name='retos', blank=True)
    completado_por = models.ManyToManyField(Usuario, related_name='retos_completados', blank=True)

    @property
    def estado_semana(self):
        hoy = timezone.localdate()
        if self.fecha_inicio <= hoy <= self.fecha_fin:
            return 'ACTIVO'
        elif hoy < self.fecha_inicio:
            return 'PROXIMO'
        return 'FINALIZADO'

    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio} - {self.fecha_fin})"