from django.contrib import admin
from .models import Usuario, Entrenamiento, EntrenamientoEjercicio, Reto, Ejercicio
admin.site.register(Usuario)
admin.site.register(Reto)
admin.site.register(EntrenamientoEjercicio)
admin.site.register(Entrenamiento)
admin.site.register(Ejercicio)
# Register your models here.
