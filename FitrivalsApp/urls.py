from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:pk>/', views.detalle_usuario, name='detalle_usuario'),
    path('entrenamientos/', views.lista_entrenamientos, name='lista_entrenamientos'),
    path('entrenamientos/<int:pk>/', views.detalle_entrenamiento, name='detalle_entrenamiento'),
    path('ejercicios/', views.lista_ejercicios, name='lista_ejercicios'),
    path('ejercicios/<int:pk>/', views.detalle_ejercicio, name='detalle_ejercicio'),
    path('retos/', views.lista_retos, name='lista_retos'),
    path('retos/<int:pk>/', views.detalle_reto, name='detalle_reto'),
]