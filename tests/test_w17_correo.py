# tests/test_w17_correo.py
from decimal import Decimal
from django.core import mail
from django.test import TestCase, override_settings

from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from productos.models import Categoria, Producto
from ventas.models import Pedido
from ventas.tasks import enviar_confirmacion_pedido, verificar_stock_bajo


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='Puro <noreply@cbtis198.edu.mx>',
    ADMINS=[('Admin ERP', 'admin@cbtis198.edu.mx')],
)
class CorreoAsyncW17Tests(TestCase):

    def setUp(self):
        ConfiguracionERP.get_instance()
        self.cliente = Cliente.objects.create(
            nombre='Juan Pérez',
            correo='juan@ejemplo.com',
        )
        self.categoria = Categoria.objects.create(nombre='General')
        self.producto = Producto.objects.create(
            nombre='Laptop Pro',
            precio=Decimal('15000.00'),
            stock=10,
            categoria=self.categoria,
            activo=True,
        )
        self.pedido = Pedido.objects.create(
            numero_pedido='PED-W17-001',
            cliente=self.cliente,
            estado='pagado',
            total_pagado=Decimal('30000.00'),
            items_snapshot=[
                {
                    'nombre': self.producto.nombre,
                    'precio': str(self.producto.precio),
                    'cantidad': 2,
                }
            ],
        )

    def test_envio_confirmacion_pedido_exitoso(self):
        res = enviar_confirmacion_pedido.delay(self.pedido.pk).get()

        self.assertEqual(res['estado'], 'ok')
        self.assertEqual(res['correo'], 'juan@ejemplo.com')
        self.assertEqual(len(mail.outbox), 1)

        correo = mail.outbox[0]
        self.assertIn('PED-W17-001', correo.subject)
        self.assertEqual(correo.to, ['juan@ejemplo.com'])
        self.assertIn('$30000.00', correo.body)
        # Verificar alternativa HTML
        self.assertEqual(len(correo.alternatives), 1)
        html, mimetype = correo.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('Laptop Pro', html)
        self.assertIn('erp-django-cbtis198.onrender.com', html)

        self.pedido.refresh_from_db()
        self.assertTrue(self.pedido.correo_enviado)

    def test_idempotencia_no_duplica_correo(self):
        # Primer envío
        enviar_confirmacion_pedido.delay(self.pedido.pk).get()
        self.assertEqual(len(mail.outbox), 1)

        # Segundo envío del mismo pedido debe omitirse
        res2 = enviar_confirmacion_pedido.delay(self.pedido.pk).get()
        self.assertEqual(res2['estado'], 'skip')
        self.assertEqual(len(mail.outbox), 1)

    def test_pedido_inexistente_retorna_error(self):
        res = enviar_confirmacion_pedido.delay(999999).get()
        self.assertEqual(res['estado'], 'error')
        self.assertEqual(len(mail.outbox), 0)

    def test_alerta_stock_bajo_envia_correo_admin(self):
        self.producto.stock = 2
        self.producto.save()

        res = verificar_stock_bajo.delay(umbral=5).get()
        self.assertEqual(res['total'], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['admin@cbtis198.edu.mx'])
        self.assertIn('Laptop Pro', mail.outbox[0].body)