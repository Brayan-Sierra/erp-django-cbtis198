"""Suite de pruebas W23 — Presupuesto de queries SQL por vista.

Verifica que las vistas críticas no superen un número máximo de
queries SQL, detectando regresiones de rendimiento.

IMPORTANTE: Estos tests usan setUp con factory_boy para crear un
conjunto de datos consistente. El número de queries esperado incluye:
  - 1 query de sesión (autenticación)
  - N queries de la vista

Si el número esperado cambia, revisar que no se introdujo un N+1.

Ejecutar con:
    python manage.py test tests.test_w23_rendimiento --verbosity=2
"""
import time

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from reportes.exports import generar_excel_ventas
from tests.factories import (
    ClienteFactory,
    DetalleVentaFactory,
    ProductoFactory,
    ProveedorFactory,
    VentaFactory,
)
from ventas.models import Venta


class ProductoListaQueryTest(TestCase):
    """Tests de presupuesto de queries en vistas de productos."""

    def setUp(self):
        self.user = User.objects.create_user('perf', password='pass')
        prov = ProveedorFactory()
        # Crear 10 productos compartiendo proveedor para evitar colisión de correo único
        self.productos = ProductoFactory.create_batch(10, proveedor=prov)
        self.client.force_login(self.user)

    def test_lista_productos_no_supera_5_queries(self):
        """GET /productos/ debe ejecutar ≤ 5 queries con 10 productos."""
        # 1. SELECT COUNT(*) (paginación)
        # 2. SELECT django_session
        # 3. SELECT auth_user
        # 4. SELECT productos_producto JOIN categoria JOIN proveedor
        with self.assertNumQueries(4):
            r = self.client.get(reverse('productos:lista'))
        self.assertEqual(r.status_code, 200)

    def test_detalle_producto_no_supera_5_queries(self):
        """GET /productos/<id>/ debe ejecutar 3 queries con select_related."""
        prod = self.productos[0]
        with self.assertNumQueries(3):
            r = self.client.get(
                reverse('productos:detalle', args=[prod.pk])
            )
        self.assertEqual(r.status_code, 200)


class VentaListaQueryTest(TestCase):
    """Tests de presupuesto de queries en vistas de ventas."""

    def setUp(self):
        self.user = User.objects.create_user('perf_venta', password='pass')
        cli = ClienteFactory()
        prod = ProductoFactory()
        # Crear 10 ventas con detalles
        for _ in range(10):
            v = VentaFactory(cliente=cli)
            DetalleVentaFactory(venta=v, producto=prod)
        self.client.force_login(self.user)

    def test_lista_ventas_con_select_related(self):
        """GET /ventas/ con 10 ventas debe ejecutar ≤ 25 queries.

        Con select_related('cliente'): 1 query para ventas+cliente.
        El total @property accede a detalles pero está paginado a 20.
        """
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(reverse('ventas:lista'))
        self.assertEqual(r.status_code, 200)
        self.assertLess(len(ctx), 25)


class ExportacionQueryTest(TestCase):
    """Tests de presupuesto de queries en la exportación."""

    def setUp(self):
        cli = ClienteFactory()
        prod = ProductoFactory()
        # Crear 20 ventas con detalles
        self.ventas_creadas = []
        for _ in range(20):
            v = VentaFactory(cliente=cli)
            DetalleVentaFactory(venta=v, producto=prod)
            self.ventas_creadas.append(v)

    def test_generar_excel_usa_prefetch(self):
        """generar_excel_ventas con prefetch debe usar ≤ 3 queries SQL."""
        queryset = (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
            .all()
        )

        with self.assertNumQueries(3):
            # 1: SELECT ventas + clientes (select_related JOIN)
            # 2: SELECT detalles WHERE venta_id IN (...)
            # 3: SELECT productos WHERE id IN (...)
            buffer = generar_excel_ventas(queryset)

        self.assertGreater(buffer.getbuffer().nbytes, 1024)

    def test_generar_excel_sin_prefetch_usa_mas_queries(self):
        """Demostrar que sin prefetch_related se generan N+1 queries.

        Este test documenta el problema ANTES del fix — verifica que
        el número de queries sin optimización es mayor que con ella.
        """
        queryset_sin_opt = (
            Venta.objects
            .select_related('cliente')
            .all()
        )

        with CaptureQueriesContext(connection) as ctx_sin:
            ventas = list(queryset_sin_opt)
            for v in ventas:
                _ = ', '.join(d.producto.nombre for d in v.detalles.all())
        queries_sin_opt = len(ctx_sin)

        queryset_con_opt = (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
            .all()
        )

        with CaptureQueriesContext(connection) as ctx_con:
            ventas_opt = list(queryset_con_opt)
            for v in ventas_opt:
                _ = ', '.join(d.producto.nombre for d in v.detalles.all())
        queries_con_opt = len(ctx_con)

        self.assertLess(queries_con_opt, queries_sin_opt)


class ReporteVentasQueryTest(TestCase):
    """Tests de presupuesto de queries en la vista de reporte."""

    def setUp(self):
        self.user = User.objects.create_user('perf_rep', password='pass')
        cli = ClienteFactory()
        prod = ProductoFactory()
        for _ in range(5):
            v = VentaFactory(cliente=cli)
            DetalleVentaFactory(venta=v, producto=prod)
        self.client.force_login(self.user)

    def test_reporte_ventas_usa_prefetch(self):
        """GET /reportes/ventas/ con 5 ventas debe usar pocas queries."""
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(reverse('reportes:reporte_ventas'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['total_filtrado'], 5)
        self.assertLessEqual(len(ctx), 10)

    def test_exportacion_excel_sincrona_descarga_rapido(self):
        """La exportación Excel síncrona debe responder en < 3 segundos."""
        t0 = time.time()
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        elapsed = time.time() - t0
        self.assertEqual(r.status_code, 200)
        self.assertLess(
            elapsed, 3.0,
            f"Exportación demoró {elapsed:.2f}s, se esperaban < 3s"
        )