import datetime

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Circulo, Ejercicio, Entrenamiento, InvitacionCirculo, Reto, Usuario


class BaseTest(TestCase):
    def setUp(self):
        self.ej = Ejercicio.objects.create(
            nombre='Sentadilla', grupo_muscular='PIERNA', dificultad='FACIL', descripcion='Baja y sube.')
        self.ana = Usuario.objects.create(nombre='ana', email='ana@test.com', password=make_password('secreto123'))
        self.beto = Usuario.objects.create(nombre='beto', email='beto@test.com', password=make_password('secreto123'))
        self.carla = Usuario.objects.create(nombre='carla', email='carla@test.com', password=make_password('secreto123'))
        self.reto = Reto.objects.create(nombre='Reto activo', puntos_recompensa=50)
        self.reto.ejercicios.add(self.ej)
        self.circulo = Circulo.objects.create(nombre='Gym', anfitrion=self.ana)
        self.circulo.miembros.add(self.ana, self.beto)

    def login(self, usuario=None):
        usuario = usuario or self.ana
        s = self.client.session
        s['usuario_id'] = usuario.id
        s['usuario_nombre'] = usuario.nombre
        s.save()


class VistasPublicasTest(BaseTest):
    def test_paginas_publicas(self):
        urls = [
            reverse('index'), reverse('lista_ejercicios'), reverse('detalle_ejercicio', args=[self.ej.pk]),
            reverse('lista_retos'), reverse('detalle_reto', args=[self.reto.pk]),
            reverse('registro_usuario'), reverse('login_usuario'),
            reverse('detalle_usuario', args=[self.ana.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_detalle_inexistente_404(self):
        self.assertEqual(self.client.get(reverse('detalle_ejercicio', args=[9999])).status_code, 404)

    def test_paginas_privadas_redirigen_a_login(self):
        for nombre in ['lista_usuarios', 'lista_circulos', 'crear_circulo', 'crear_entrenamiento']:
            with self.subTest(vista=nombre):
                self.assertRedirects(self.client.get(reverse(nombre)), reverse('login_usuario'))

    def test_paginas_privadas_con_sesion(self):
        self.login()
        for nombre in ['lista_usuarios', 'lista_circulos', 'crear_circulo', 'crear_entrenamiento']:
            with self.subTest(vista=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)


class AutenticacionTest(BaseTest):
    def test_login_correcto_e_incorrecto(self):
        r = self.client.post(reverse('login_usuario'), {'nombre': 'ana', 'password': 'mala'})
        self.assertContains(r, 'incorrectos')
        r = self.client.post(reverse('login_usuario'), {'nombre': 'ana', 'password': 'secreto123'})
        self.assertRedirects(r, reverse('index'))

    def test_registro_guarda_password_hasheada(self):
        self.client.post(reverse('registro_usuario'),
                         {'nombre': 'bea', 'email': 'bea@test.com', 'password': 'clave-muy-segura-91'})
        self.assertTrue(Usuario.objects.get(nombre='bea').password.startswith('pbkdf2_'))

    def test_registro_rechaza_password_debil(self):
        self.client.post(reverse('registro_usuario'),
                         {'nombre': 'bea', 'email': 'bea@test.com', 'password': '1234'})
        self.assertFalse(Usuario.objects.filter(nombre='bea').exists())

    def test_logout_solo_por_post(self):
        self.login()
        self.assertEqual(self.client.get(reverse('logout_usuario')).status_code, 405)
        self.client.post(reverse('logout_usuario'))
        self.assertNotIn('usuario_id', self.client.session)


class CompletarRetoTest(BaseTest):
    def url(self):
        return reverse('completar_reto', args=[self.reto.pk])

    def test_requiere_login(self):
        self.assertRedirects(self.client.post(self.url()), reverse('login_usuario'))

    def test_suma_puntos_una_sola_vez(self):
        self.login()
        self.client.post(self.url())
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.puntos, 50)
        self.client.post(self.url())
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.puntos, 50)

    def test_reto_finalizado_no_se_puede_completar(self):
        self.login()
        self.reto.fecha_inicio = timezone.localdate() - datetime.timedelta(days=20)
        self.reto.fecha_fin = timezone.localdate() - datetime.timedelta(days=10)
        self.reto.save()
        self.client.post(self.url())
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.puntos, 0)

    def test_ajax_devuelve_json(self):
        self.login()
        cabecera = {'X-Requested-With': 'XMLHttpRequest'}
        r = self.client.post(self.url(), headers=cabecera)
        self.assertTrue(r.json()['ok'])
        r = self.client.post(self.url(), headers=cabecera)
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()['ok'])


class CirculosTest(BaseTest):
    def test_invitar_crea_invitacion_pendiente(self):
        self.login()
        self.client.post(reverse('invitar_circulo'), {'circulo_id': self.circulo.pk, 'invitado_id': self.carla.pk})
        inv = InvitacionCirculo.objects.get(circulo=self.circulo, invitado=self.carla)
        self.assertEqual(inv.estado, 'PENDIENTE')

    def test_solo_el_anfitrion_puede_invitar(self):
        self.login(self.beto)
        r = self.client.post(reverse('invitar_circulo'), {'circulo_id': self.circulo.pk, 'invitado_id': self.carla.pk})
        self.assertEqual(r.status_code, 404)

    def test_invitar_no_redirige_a_sitios_externos(self):
        self.login()
        r = self.client.post(reverse('invitar_circulo'), {
            'circulo_id': self.circulo.pk, 'invitado_id': self.carla.pk, 'next': 'https://malo.example.com/'})
        self.assertRedirects(r, reverse('detalle_circulo', args=[self.circulo.pk]))

    def test_aceptar_invitacion_anade_miembro(self):
        inv = InvitacionCirculo.objects.create(circulo=self.circulo, invitado=self.carla)
        self.login(self.carla)
        self.client.post(reverse('responder_invitacion', args=[inv.pk]), {'accion': 'aceptar'})
        self.assertTrue(self.circulo.miembros.filter(pk=self.carla.pk).exists())

    def test_no_miembro_no_ve_el_circulo(self):
        self.login(self.carla)
        self.assertRedirects(self.client.get(reverse('detalle_circulo', args=[self.circulo.pk])), reverse('lista_circulos'))


class PrivacidadEntrenamientosTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.ent = Entrenamiento.objects.create(usuario=self.ana, fecha=timezone.localdate(), duracion_minutos=30)

    def test_anonimo_no_ve_entrenamientos(self):
        self.assertRedirects(self.client.get(reverse('detalle_entrenamiento', args=[self.ent.pk])), reverse('login_usuario'))

    def test_miembro_del_circulo_si_lo_ve(self):
        self.login(self.beto)
        self.assertEqual(self.client.get(reverse('detalle_entrenamiento', args=[self.ent.pk])).status_code, 200)

    def test_ajeno_al_circulo_no_lo_ve(self):
        self.login(self.carla)
        self.assertRedirects(self.client.get(reverse('detalle_entrenamiento', args=[self.ent.pk])), reverse('lista_circulos'))


class EjercicioInfoTest(BaseTest):
    def test_devuelve_json_con_descripcion_y_retos(self):
        r = self.client.get(reverse('ejercicio_info', args=[self.ej.pk]))
        datos = r.json()
        self.assertEqual(datos['nombre'], 'Sentadilla')
        self.assertEqual(datos['descripcion'], 'Baja y sube.')
        self.assertEqual(datos['retos'], ['Reto activo'])

    def test_ejercicio_inexistente(self):
        self.assertEqual(self.client.get(reverse('ejercicio_info', args=[9999])).status_code, 404)


class ModelosTest(BaseTest):
    def test_fechas_por_defecto_son_la_semana_actual(self):
        self.assertEqual(self.reto.estado_semana, 'ACTIVO')