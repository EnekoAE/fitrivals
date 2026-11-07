from django.contrib import admin
from .models import Usuario, Ejercicio, Entrenamiento, EntrenamientoEjercicio, Reto

class EntrenamientoEjercicioInline(admin.TabularInline):
    model = EntrenamientoEjercicio
    extra = 1

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'puntos', 'fecha_alta')
    search_fields = ('nombre', 'email')

@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo_muscular', 'dificultad')
    list_filter = ('grupo_muscular', 'dificultad')

@admin.register(Entrenamiento)
class EntrenamientoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'duracion_minutos')
    list_filter = ('fecha', 'usuario')
    inlines = [EntrenamientoEjercicioInline]

@admin.register(Reto)
class RetoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puntos_recompensa')