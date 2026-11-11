from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from clientes.models import Cliente
from productos.models import Categoria, Producto
from ventas.models import Venta, DetalleVenta
from configuracion.models import ConfiguracionERP


class DocumentosW12Test(TestCase):
    def setUp(self):
        ConfiguracionERP.get_instance()
        self.user = User.objects.create_user('docuser', password='password123')
        cat = Categoria.objects.create(nombre='Cat W12')
        prod = Producto.objects.create(nombre='Prod W12', precio=Decimal('150.00'), stock=10, categoria=cat)
        cli = Cliente.objects.create(nombre='Cli W12', correo='cli@w12.com')
        self.venta = Venta.objects.create(cliente=cli)
        DetalleVenta.objects.create(
            venta=self.venta,
            producto=prod,
            cantidad=2,
            precio_unitario=Decimal('150.00')
        )

    def test_pdf_requiere_autenticacion(self):
        response = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertEqual(response.status_code, 302)

    def test_pdf_generacion_correcta_xhtml2pdf(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('ventas:pdf', args=[self.venta.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/pdf', response['Content-Type'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_excel_exportacion_correcta_openpyxl(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('productos:exportar_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])