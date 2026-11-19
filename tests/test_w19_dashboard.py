"""Suite de pruebas W19 — Dashboard, KPIs y caché Redis.

Usa el backend locmem para los tests (no requiere Redis real)
y verifica tanto los cálculos de KPIs como el comportamiento
del caché con cache.get_or_set().

Ejecutar con:
    python manage.py test tests.test_w19_dashboard --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clientes.models   import Cliente
from productos.models  import Categoria, Producto
from ventas.models     import DetalleVenta, Pedido, Venta

from reportes.views import CACHE_KEY_DASHBOARD, _calcular_kpis

CACHE_TEST = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}


class DashboardAutenticacionTest(TestCase):
    """Tests de protección del dashboard."""

    def test_dashboard_sin_auth_redirige_a_login(self):
        """GET /reportes/ sin login → 302 a /accounts/login/."""
        r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_dashboard_con_auth_devuelve_200(self):
        """GET /reportes/ con login → 200."""
        user = User.objects.create_user('repuser', password='pass')
        self.client.force_login(user)
        with override_settings(CACHES=CACHE_TEST):
            cache.clear()
            r = self.client.get(reverse('reportes:inicio'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'reportes/dashboard.html')


@override_settings(CACHES=CACHE_TEST)
class CalcularKPIsTest(TestCase):
    """Tests de la función _calcular_kpis()."""

    def setUp(self):
        cache.clear()
        cat        = Categoria.objects.create(nombre='Cat KPI')
        self.prod  = Producto.objects.create(
            nombre='Producto KPI', precio=Decimal('200.00'),
            stock=2, categoria=cat   # stock < 5 → cuenta como crítico
        )
        self.cli   = Cliente.objects.create(
            nombre='Cliente KPI', correo='kpi@test.com'
        )

    def test_kpis_incluye_las_5_claves(self):
        """El dict de KPIs debe incluir las 5 métricas principales."""
        kpis = _calcular_kpis()
        for clave in ['ventas_dia_total', 'clientes_nuevos',
                      'stock_critico', 'pedidos_pendientes',
                      'revenue_mensual']:
            self.assertIn(clave, kpis)

    def test_stock_critico_detecta_producto_bajo(self):
        """Producto con stock=2 (< 5) debe contarse en stock_critico."""
        kpis = _calcular_kpis()
        self.assertGreaterEqual(kpis['stock_critico'], 1)

    def test_pedidos_pendientes_cuenta_correctamente(self):
        """Un pedido en estado 'pendiente' debe sumar al KPI."""
        Pedido.objects.create(
            numero_pedido='PED-KPI-001', cliente=self.cli,
            estado='pendiente', total_pagado=Decimal('200.00')
        )
        kpis = _calcular_kpis()
        self.assertEqual(kpis['pedidos_pendientes'], 1)

    def test_ventas_dia_suma_pedidos_pagados_hoy(self):
        """Ventas del día = suma de total_pagado de pedidos pagados hoy."""
        Pedido.objects.create(
            numero_pedido='PED-KPI-002', cliente=self.cli,
            estado='pagado', total_pagado=Decimal('350.00')
        )
        kpis = _calcular_kpis()
        self.assertEqual(kpis['ventas_dia_total'], '350.00')

    def test_top_productos_incluye_producto_vendido(self):
        """El producto con ventas debe aparecer en labels_productos."""
        venta = Venta.objects.create(cliente=self.cli)
        DetalleVenta.objects.create(
            venta=venta, producto=self.prod,
            cantidad=3, precio_unitario=Decimal('200.00')
        )
        kpis = _calcular_kpis()
        self.assertIn('Producto KPI', kpis['labels_productos'])


@override_settings(CACHES=CACHE_TEST)
class CacheDashboardTest(TestCase):
    """Tests del comportamiento de cache.get_or_set()."""

    def setUp(self):
        cache.clear()

    def test_segunda_llamada_no_recalcula(self):
        """Con caché activo, la segunda llamada no debe invocar
        de nuevo a _calcular_kpis()."""
        with patch(
            'reportes.views._calcular_kpis',
            wraps=_calcular_kpis
        ) as mock_calc:
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            # _calcular_kpis solo debe haberse ejecutado UNA vez
            self.assertEqual(mock_calc.call_count, 1)

    def test_cache_clear_fuerza_recalculo(self):
        """Tras cache.delete(), la siguiente llamada SÍ recalcula."""
        with patch(
            'reportes.views._calcular_kpis',
            wraps=_calcular_kpis
        ) as mock_calc:
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            cache.delete(CACHE_KEY_DASHBOARD)
            cache.get_or_set(CACHE_KEY_DASHBOARD, mock_calc, 300)
            self.assertEqual(mock_calc.call_count, 2)