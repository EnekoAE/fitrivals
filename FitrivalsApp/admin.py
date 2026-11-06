from django.contrib import admin
from .models import Usuario, Entrenamiento, EntrenamientoEjercicio, Reto
admin.site.register(Usuario)
admin.site.register(Reto)
admin.site.register(EntrenamientoEjercicio)
admin.site.register(Entrenamiento)
# Register your models here.
