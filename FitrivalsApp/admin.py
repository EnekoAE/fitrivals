from django.contrib import admin
from django.contrib.auth.hashers import make_password, identify_hasher
from .models import Usuario, Ejercicio, Entrenamiento, EntrenamientoEjercicio, Reto


class EntrenamientoEjercicioInline(admin.TabularInline):
    model = EntrenamientoEjercicio
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'puntos', 'fecha_alta')
    search_fields = ('nombre', 'email')

    def save_model(self, request, obj, form, change):
        # Si la contraseña no tiene formato cifrado de Django, la encriptamos antes de guardar
        try:
            identify_hasher(obj.password)
        except ValueError:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'grupo_muscular', 'dificultad')
    list_filter = ('grupo_muscular', 'dificultad')


@admin.register(Entrenamiento)
class EntrenamientoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'reto', 'duracion_minutos')
    list_filter = ('fecha', 'usuario')
    inlines = [EntrenamientoEjercicioInline]


@admin.register(Reto)
class RetoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'puntos_recompensa')
    list_filter = ('fecha_inicio', 'fecha_fin')
    filter_horizontal = ('ejercicios', 'completado_por')