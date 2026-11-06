from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/<int:pk>/', views.detalle_usuario, name='detalle_usuario'),
]