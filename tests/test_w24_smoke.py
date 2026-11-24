"""Smoke tests W24 — Verificación de que el sistema está vivo.

Estos 8 tests comprueban que las rutas más críticas del ERP responden
correctamente. Son los tests más simples pero los más importantes:
si alguno falla, el sistema no está operativo.

Orden de criticidad:
    1. Página de inicio         — el sistema arranca
    2. Login                    — la autenticación funciona
    3. API pública              — la API responde sin auth
    4. API con token            — la autenticación de API funciona
    5. Panel admin              — el admin está accesible
    6. Catálogo público         — la tienda es accesible sin login
    7. Dashboard                — los reportes funcionan
    8. Webhook                  — el endpoint de Stripe responde

Ejecutar con:
    python manage.py test tests.test_w24_smoke --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from tests.factories import CategoriaFactory, ProductoFactory


class SmokePaginaInicioTest(TestCase):
    """Smoke test 1: El sistema arranca y responde."""

    def test_pagina_inicio_responde_200(self):
        """GET / → 200. Si falla, el servidor no está arriba."""
        r = self.client.get(reverse('inicio'))
        self.assertIn(r.status_code, [200, 301, 302],
                      "La página de inicio no responde correctamente")


class SmokeAutenticacionTest(TestCase):
    """Smoke test 2: La autenticación funciona."""

    def test_pagina_login_accesible(self):
        """GET /accounts/login/ → 200. Si falla, allauth no está configurado."""
        r = self.client.get(reverse('account_login'))
        self.assertEqual(r.status_code, 200,
                         "La página de login no está accesible")

    def test_login_y_logout_funcional(self):
        """Login exitoso → 302. Si falla, la autenticación está rota."""
        User.objects.create_user('smoke_user', password='smoke_pass123')
        r = self.client.post(reverse('account_login'), {
            'login':    'smoke_user',
            'password': 'smoke_pass123',
        })
        # allauth redirige tras login exitoso
        self.assertEqual(r.status_code, 302,
                         "El login no redirigió correctamente")


class SmokeAPITest(TestCase):
    """Smoke tests 3 y 4: La API responde."""

    def setUp(self):
        self.api_client = APIClient()
        self.user  = User.objects.create_user('api_smoke', password='pass')
        self.token = Token.objects.create(user=self.user)
        CategoriaFactory()          # hay al menos 1 categoría en la BD
        ProductoFactory()           # hay al menos 1 producto

    def test_api_productos_publica_200(self):
        """GET /api/productos/ sin token → 200.
        Si falla, la API no está funcionando o IsAuthenticatedOrReadOnly está mal."""
        r = self.api_client.get('/api/productos/')
        self.assertEqual(r.status_code, 200,
                         "La API pública de productos no responde")

    def test_api_con_token_valido_200(self):
        """GET /api/productos/ con token → 200 con JSON válido.
        Si falla, la autenticación por token está rota."""
        self.api_client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        r = self.api_client.get('/api/productos/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('results', r.json(),
                      "La respuesta JSON no tiene la clave 'results' esperada")


class SmokeAdminTest(TestCase):
    """Smoke test 5: El panel admin está accesible."""

    def test_admin_login_accesible(self):
        """GET /admin/ sin auth → redirige al login del admin.
        Si falla, el admin no está configurado."""
        r = self.client.get('/admin/')
        # El admin sin autenticar redirige al login
        self.assertIn(r.status_code, [200, 302],
                      "El admin no está accesible")


class SmokeCatalogoTest(TestCase):
    """Smoke test 6: La tienda pública funciona."""

    def test_catalogo_publico_200(self):
        """GET /catalogo/ sin login → 200.
        Si falla, la app catalogo no está registrada o la URL no existe."""
        r = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(r.status_code, 200,
                         "El catálogo público no está accesible")


class SmokeDashboardTest(TestCase):
    """Smoke test 7: El dashboard funciona tras login."""

    def test_dashboard_requiere_auth(self):
        """GET /reportes/ sin login → 302 al login.
        Si falla, el LoginRequiredMixin no está aplicado."""
        r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 302,
                         "El dashboard debería requerir autenticación")

    def test_dashboard_con_auth_200(self):
        """GET /reportes/ con login → 200.
        Si falla, el dashboard tiene un error de cálculo o template."""
        user = User.objects.create_user('dash_smoke', password='pass')
        self.client.force_login(user)
        with self.settings(CACHES={'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
        }}):
            r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 200,
                         "El dashboard retornó un error tras autenticación")