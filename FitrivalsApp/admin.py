from django.contrib import admin
from django.contrib.auth.hashers import make_password, identify_hasher
from .models import Usuario, Circulo, InvitacionCirculo, Ejercicio, Entrenamiento, EntrenamientoEjercicio, Reto


class EntrenamientoEjercicioInline(admin.TabularInline):
    model = EntrenamientoEjercicio
    extra = 1


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'puntos', 'fecha_alta')
    search_fields = ('nombre', 'email')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('password',)
        return ()

    def save_model(self, request, obj, form, change):
        try:
            identify_hasher(obj.password)
        except ValueError:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Circulo)
class CirculoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'anfitrion', 'fecha_creacion')
    search_fields = ('nombre', 'anfitrion__nombre')
    filter_horizontal = ('miembros',)


@admin.register(InvitacionCirculo)
class InvitacionCirculoAdmin(admin.ModelAdmin):
    list_display = ('circulo', 'invitado', 'estado', 'fecha_envio')
    list_filter = ('estado', 'circulo')


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