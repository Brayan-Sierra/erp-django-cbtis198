"""Suite de pruebas W21 — django-simple-history en Producto y Venta.

Verifica que el historial se crea automáticamente al guardar,
que los tipos de cambio son correctos, y que la vista de
historial funciona correctamente.

Ejecutar con:
    python manage.py test tests.test_w21_historico --verbosity=2

Resultado esperado:
    Ran 8 tests in X.XXXs
    OK
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from clientes.models    import Cliente
from productos.models   import Categoria, Producto
from ventas.models      import Pedido, Venta


class HistorialProductoModelTest(TestCase):
    """Tests del historial automático en el modelo Producto."""

    def setUp(self):
        self.cat = Categoria.objects.create(nombre='Cat Hist')

    def test_historia_creada_al_crear_producto(self):
        """Al crear un Producto, debe haber 1 registro en su historial."""
        prod = Producto.objects.create(
            nombre='Laptop', precio=Decimal('10000.00'),
            stock=5, categoria=self.cat
        )
        self.assertEqual(prod.history.count(), 1)

    def test_history_type_creacion_es_mas(self):
        """El primer registro histórico debe ser de tipo '+' (creación)."""
        prod = Producto.objects.create(
            nombre='Mouse', precio=Decimal('250.00'),
            stock=20, categoria=self.cat
        )
        # history.last() = el más antiguo (la creación)
        self.assertEqual(prod.history.last().history_type, '+')

    def test_historia_actualizada_al_cambiar_precio(self):
        """Al cambiar el precio, el historial debe tener 2 registros."""
        prod = Producto.objects.create(
            nombre='Teclado', precio=Decimal('500.00'),
            stock=10, categoria=self.cat
        )
        prod.precio = Decimal('450.00')
        prod.save()
        self.assertEqual(prod.history.count(), 2)

    def test_history_type_edicion_es_virgulilla(self):
        """El registro de edición debe ser de tipo '~' (modificación)."""
        prod = Producto.objects.create(
            nombre='Monitor', precio=Decimal('3000.00'),
            stock=3, categoria=self.cat
        )
        prod.stock = 8
        prod.save()
        # history.first() = el más reciente (la edición)
        self.assertEqual(prod.history.first().history_type, '~')

    def test_precio_en_historia_refleja_valor_historico(self):
        """El historial debe conservar el precio original, no el nuevo."""
        prod = Producto.objects.create(
            nombre='Impresora', precio=Decimal('1200.00'),
            stock=2, categoria=self.cat
        )
        precio_original = Decimal('1200.00')
        prod.precio = Decimal('999.00')
        prod.save()
        # El registro más antiguo (la creación) debe tener el precio original
        self.assertEqual(prod.history.last().precio, precio_original)

    def test_diff_against_detecta_cambio_de_precio(self):
        """diff_against debe identificar el campo 'precio' como cambiado."""
        prod = Producto.objects.create(
            nombre='Tablet', precio=Decimal('5000.00'),
            stock=4, categoria=self.cat
        )
        prod.precio = Decimal('4500.00')
        prod.save()
        nuevo   = prod.history.first()
        antiguo = prod.history.last()
        delta   = nuevo.diff_against(antiguo)
        campos_cambiados = [c.field for c in delta.changes]
        self.assertIn('precio', campos_cambiados)


class HistoricoVistaTest(TestCase):
    """Tests de la vista HistoricoProductoView."""

    def setUp(self):
        self.user = User.objects.create_user('histuser', password='pass')
        cat        = Categoria.objects.create(nombre='Cat Vista')
        self.prod  = Producto.objects.create(
            nombre='Camara', precio=Decimal('8000.00'),
            stock=2, categoria=cat
        )

    def test_historico_sin_auth_redirige_a_login(self):
        """GET /productos/<id>/historico/ sin login → 302."""
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_historico_con_auth_devuelve_200(self):
        """GET /productos/<id>/historico/ con login → 200."""
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'productos/historico.html')

    def test_historico_muestra_registros_en_contexto(self):
        """El contexto debe incluir los registros históricos."""
        self.prod.precio = Decimal('7500.00')
        self.prod.save()
        self.client.force_login(self.user)
        r = self.client.get(
            reverse('productos:historico', args=[self.prod.pk])
        )
        self.assertIn('registros', r.context)
        self.assertEqual(len(r.context['registros']), 2)