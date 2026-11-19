"""Suite de pruebas W20 — Reportes filtrables y exportación adaptativa.

Verifica filtros del reporte de ventas y ambas rutas de exportación
(síncrona y asíncrona), usando mock para forzar el umbral asíncrono
sin necesidad de crear 1000+ registros reales.

Ejecutar con:
    python manage.py test tests.test_w20_reportes --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from clientes.models   import Cliente
from configuracion.models import ConfiguracionERP
from productos.models  import Categoria, Producto
from reportes.models   import ExportacionReporte
from reportes.tasks    import generar_exportacion_async
from ventas.models     import DetalleVenta, Venta


EMAIL_SETTINGS = {
    'EMAIL_BACKEND':                'django.core.mail.backends.locmem.EmailBackend',
    'CELERY_TASK_ALWAYS_EAGER':     True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'DEFAULT_FROM_EMAIL':           'test@erp.com',
}


def _crear_venta(cliente, producto, cantidad=1) -> Venta:
    """Crea una venta de prueba con una línea de detalle."""
    venta = Venta.objects.create(cliente=cliente)
    DetalleVenta.objects.create(
        venta=venta, producto=producto,
        cantidad=cantidad, precio_unitario=producto.precio
    )
    return venta


class ReporteFiltrosTest(TestCase):
    """Tests del filtrado en ReporteVentasView."""

    def setUp(self):
        self.user = User.objects.create_user('repuser', password='pass')
        cat            = Categoria.objects.create(nombre='Cat Rep')
        self.prod      = Producto.objects.create(
            nombre='Producto A', precio=Decimal('100.00'),
            stock=10, categoria=cat
        )
        self.otro_prod = Producto.objects.create(
            nombre='Producto B', precio=Decimal('50.00'),
            stock=10, categoria=cat
        )
        self.cli_a = Cliente.objects.create(nombre='Cliente A', correo='a@t.com')
        self.cli_b = Cliente.objects.create(nombre='Cliente B', correo='b@t.com')

        _crear_venta(self.cli_a, self.prod, cantidad=2)
        _crear_venta(self.cli_b, self.otro_prod, cantidad=1)

        self.client.force_login(self.user)

    def test_reporte_sin_auth_redirige_a_login(self):
        """GET /reportes/ventas/ sin login → 302."""
        self.client.logout()
        r = self.client.get(reverse('reportes:reporte_ventas'))
        self.assertEqual(r.status_code, 302)

    def test_filtro_por_cliente(self):
        """Filtrar por cliente debe devolver solo sus ventas."""
        r = self.client.get(
            reverse('reportes:reporte_ventas'),
            {'cliente': self.cli_a.pk}
        )
        ventas = list(r.context['ventas'])
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0].cliente, self.cli_a)

    def test_filtro_por_producto(self):
        """Filtrar por producto debe devolver solo ventas con ese producto."""
        r = self.client.get(
            reverse('reportes:reporte_ventas'),
            {'producto': self.prod.pk}
        )
        ventas = list(r.context['ventas'])
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0].cliente, self.cli_a)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExportacionSincronaTest(TestCase):
    """Tests de la exportación síncrona (≤ UMBRAL_ASYNC filas)."""

    def setUp(self):
        self.user = User.objects.create_user('expuser', password='pass')
        cat        = Categoria.objects.create(nombre='Cat Exp')
        prod       = Producto.objects.create(
            nombre='Prod Exp', precio=Decimal('200.00'),
            stock=5, categoria=cat
        )
        cli        = Cliente.objects.create(nombre='Cli Exp', correo='exp@t.com')
        _crear_venta(cli, prod)
        self.client.force_login(self.user)

    def test_exportar_excel_descarga_inmediata(self):
        """Con pocas filas, exportar Excel debe descargar de inmediato."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('spreadsheetml', r.get('Content-Type', ''))

    def test_exportar_pdf_descarga_inmediata(self):
        """Con pocas filas, exportar PDF debe descargar de inmediato."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'pdf'}
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn('application/pdf', r.get('Content-Type', ''))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), **EMAIL_SETTINGS)
class ExportacionAsincronaTest(TestCase):
    """Tests de la exportación asíncrona (> UMBRAL_ASYNC filas, simulado)."""

    def setUp(self):
        mail.outbox = []
        ConfiguracionERP.get_instance()
        self.user = User.objects.create_user(
            'asyncuser', password='pass', email='async@test.com'
        )
        cat        = Categoria.objects.create(nombre='Cat Async')
        self.prod  = Producto.objects.create(
            nombre='Prod Async', precio=Decimal('300.00'),
            stock=5, categoria=cat
        )
        cli        = Cliente.objects.create(nombre='Cli Async', correo='ca@t.com')
        _crear_venta(cli, self.prod)
        self.client.force_login(self.user)

    @patch('reportes.views.UMBRAL_ASYNC', 0)   # fuerza la ruta async
    def test_exportar_supera_umbral_crea_registro_pendiente(self):
        """Si el total supera el umbral, se crea ExportacionReporte."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        self.assertEqual(ExportacionReporte.objects.count(), 1)
        exportacion = ExportacionReporte.objects.first()
        self.assertFalse(exportacion.completado)
        self.assertEqual(r.status_code, 302)   # redirect a página de espera

    def test_tarea_genera_archivo_y_marca_completado(self):
        """generar_exportacion_async debe generar el archivo y marcar listo."""
        exportacion = ExportacionReporte.objects.create(
            usuario=self.user, formato='excel', filtros={}
        )
        generar_exportacion_async.delay(exportacion.pk)

        exportacion.refresh_from_db()
        self.assertTrue(exportacion.completado)
        self.assertTrue(bool(exportacion.archivo))

    def test_tarea_envia_correo_con_link_descarga(self):
        """Al completar, debe enviarse un correo con el link al usuario."""
        exportacion = ExportacionReporte.objects.create(
            usuario=self.user, formato='pdf', filtros={}
        )
        generar_exportacion_async.delay(exportacion.pk)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('async@test.com', mail.outbox[0].to)
        self.assertIn('http', mail.outbox[0].body)

    @patch('reportes.views.UMBRAL_ASYNC', 0)   # fuerza la ruta async
    @patch('reportes.tasks.generar_exportacion_async.delay')
    def test_exportar_supera_umbral_crea_registro_pendiente(self, mock_delay):
        """Si el total supera el umbral, se crea ExportacionReporte."""
        r = self.client.get(
            reverse('reportes:exportar'), {'formato': 'excel'}
        )
        self.assertEqual(ExportacionReporte.objects.count(), 1)
        exportacion = ExportacionReporte.objects.first()
        self.assertFalse(exportacion.completado)
        self.assertEqual(r.status_code, 302)   # redirect a página de espera
        mock_delay.assert_called_once_with(exportacion.pk)