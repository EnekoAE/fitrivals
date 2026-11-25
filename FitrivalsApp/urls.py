from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Portal de Usuarios
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('login/', views.login_usuario, name='login_usuario'),
    path('logout/', views.logout_usuario, name='logout_usuario'),

    # Directorio de Atletas y Perfil
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:pk>/', views.detalle_usuario, name='detalle_usuario'),

    # Círculos e Invitaciones
    path('circulos/', views.lista_circulos, name='lista_circulos'),
    path('circulos/nuevo/', views.crear_circulo, name='crear_circulo'),
    path('circulos/<int:pk>/', views.detalle_circulo, name='detalle_circulo'),
    path('circulos/invitar/', views.invitar_circulo, name='invitar_circulo'),
    path('invitaciones/<int:pk>/responder/', views.responder_invitacion, name='responder_invitacion'),

    # Ejercicios
    path('ejercicios/', views.lista_ejercicios, name='lista_ejercicios'),
    path('ejercicios/<int:pk>/', views.detalle_ejercicio, name='detalle_ejercicio'),

    # Entrenamientos
    path('entrenamientos/', views.lista_entrenamientos, name='lista_entrenamientos'),
    path('entrenamientos/nuevo/', views.crear_entrenamiento, name='crear_entrenamiento'),
    path('entrenamientos/<int:pk>/', views.detalle_entrenamiento, name='detalle_entrenamiento'),

    # Retos Semanales
    path('retos/', views.RetoListView.as_view(), name='lista_retos'),
    path('retos/<int:pk>/', views.RetoDetailView.as_view(), name='detalle_reto'),
    path('retos/<int:pk>/completar/', views.completar_reto, name='completar_reto'),
]