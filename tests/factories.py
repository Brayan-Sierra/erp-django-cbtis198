# tests/factories.py
"""Factories con datos realistas para los tests del ERP Django.

Usan factory_boy + Faker (locale es_MX) para generar instancias
de los modelos principales con datos verosímiles.

Uso básico:
    from tests.factories import ProductoFactory, VentaFactory

    prod  = ProductoFactory()
    venta = VentaFactory()
    venta = VentaFactory(cliente__nombre='Juan')          # override FK
    prods = ProductoFactory.create_batch(10, stock=0)     # batch creation
"""
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, fuzzy

from clientes.models      import Cliente
from configuracion.models import ConfiguracionERP
from productos.models     import Categoria, Producto
from proveedores.models   import Proveedor
from ventas.models        import DetalleVenta, Pedido, Venta


class CategoriaFactory(DjangoModelFactory):
    """Factory para Categoria."""

    class Meta:
        model = Categoria
        # django_get_or_create: si ya existe una Categoria con ese nombre,
        # devuelve la existente en lugar de crear un duplicado.
        django_get_or_create = ('nombre',)

    nombre      = Faker('word', locale='es_MX')
    descripcion = Faker('sentence', nb_words=6, locale='es_MX')


class ProveedorFactory(DjangoModelFactory):
    """Factory para Proveedor con datos mexicanos realistas."""

    class Meta:
        model = Proveedor

    nombre   = Faker('company', locale='es_MX')
    contacto = Faker('name', locale='es_MX')
    correo   = factory.Sequence(lambda n: f'proveedor{n}@erp-test.com')
    telefono = Faker('phone_number', locale='es_MX')
    activo   = True


class ProductoFactory(DjangoModelFactory):
    """Factory para Producto con precio y stock aleatorios."""

    class Meta:
        model = Producto

    nombre    = Faker('catch_phrase', locale='es_MX')
    precio    = factory.LazyFunction(
        lambda: Decimal(str(fuzzy.FuzzyDecimal(50.0, 15000.0, precision=2).fuzz()))
    )
    stock     = fuzzy.FuzzyInteger(1, 100)
    categoria = SubFactory(CategoriaFactory)
    proveedor = SubFactory(ProveedorFactory)
    activo    = True


class ProductoBajoStockFactory(ProductoFactory):
    """Factory para Producto con stock crítico (< 5)."""
    stock = fuzzy.FuzzyInteger(0, 4)


class ClienteFactory(DjangoModelFactory):
    """Factory para Cliente con datos mexicanos realistas."""

    class Meta:
        model = Cliente

    nombre   = Faker('name', locale='es_MX')
    correo   = factory.Sequence(lambda n: f'cliente{n}@erp-test.com')
    telefono = Faker('phone_number', locale='es_MX')
    activo   = True


class VentaFactory(DjangoModelFactory):
    """Factory para Venta — crea el encabezado sin líneas de detalle.

    Para crear ventas con líneas, usar VentaConDetallesFactory
    o agregar DetalleVentaFactory manualmente.
    """

    class Meta:
        model = Venta

    cliente = SubFactory(ClienteFactory)


class DetalleVentaFactory(DjangoModelFactory):
    """Factory para DetalleVenta vinculada a una Venta y Producto."""

    class Meta:
        model = DetalleVenta

    venta           = SubFactory(VentaFactory)
    producto        = SubFactory(ProductoFactory)
    cantidad        = fuzzy.FuzzyInteger(1, 5)
    precio_unitario = factory.LazyAttribute(lambda o: o.producto.precio)


class PedidoFactory(DjangoModelFactory):
    """Factory para Pedido."""

    class Meta:
        model = Pedido

    numero_pedido  = factory.Sequence(lambda n: f'PED-TEST-{n:04d}')
    cliente        = SubFactory(ClienteFactory)
    estado         = 'pendiente'
    total_pagado   = factory.LazyFunction(
        lambda: Decimal(str(fuzzy.FuzzyDecimal(100.0, 5000.0, precision=2).fuzz()))
    )
    items_snapshot = factory.List([])
    correo_enviado = False


class ConfiguracionERPFactory(DjangoModelFactory):
    """Factory para la configuración singleton del ERP.

    Usa pk=1 para respetar el patrón singleton.
    En los tests que requieran ConfiguracionERP, llamar a
    ConfiguracionERP.get_instance() en su lugar (es idempotente).
    """

    class Meta:
        model = ConfiguracionERP
        django_get_or_create = ('pk',)

    pk              = 1
    nombre_empresa  = 'ERP Django Test — UTEC'
    moneda          = 'MXN'
    iva_porcentaje  = Decimal('16.00')