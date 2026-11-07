from django.db import models

class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
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
        return self.nombre


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
    puntos_recompensa = models.IntegerField(default=50)

    def __str__(self):
        return f"{self.nombre} ({self.puntos_recompensa} pts)"