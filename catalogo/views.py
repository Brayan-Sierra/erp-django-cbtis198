"""Vistas del módulo de catálogo y carrito — W13/W14/W15.

Módulo público (no requiere autenticación para lectura).
El carrito se almacena en la sesión Django.
"""
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from productos.models import Producto
from ventas.models import DetalleVenta, Pedido

from .checkout_utils import (
    armar_items,
    calcular_totales,
    generar_numero_pedido,
    obtener_o_crear_cliente,
)
from .filters import ProductoFilter

# Configurar la clave secreta de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# ── CATÁLOGO ───────────────────────────────────────────────────────────────

class CatalogoView(ListView):
    """Catálogo público de productos con filtros."""

    model               = Producto
    template_name       = 'catalogo/catalogo.html'
    context_object_name = 'productos'
    paginate_by         = 12

    def get_queryset(self):
        """Filtra productos activos aplicando los filtros del request."""
        qs = (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )
        self.filtro = ProductoFilter(self.request.GET, queryset=qs)
        return self.filtro.qs

    def get_context_data(self, **kwargs):
        """Agrega el objeto filtro al contexto para renderizar el formulario."""
        ctx = super().get_context_data(**kwargs)
        ctx['filtro']     = self.filtro
        ctx['categorias'] = self.filtro.form.fields['categoria'].queryset
        return ctx


# ── CARRITO ─────────────────────────────────────────────────────────────────

def _obtener_carrito(request: object) -> dict:
    """Obtiene el carrito de la sesión o crea uno vacío."""
    return request.session.get('carrito', {})


def _guardar_carrito(request: object, carrito: dict) -> None:
    """Guarda el carrito en la sesión y marca como modificado."""
    request.session['carrito']  = carrito
    request.session.modified    = True


def ver_carrito(request):
    """Muestra el contenido del carrito con el total calculado."""
    carrito = _obtener_carrito(request)

    items = []
    total = Decimal('0.00')

    for prod_id, datos in carrito.items():
        precio    = Decimal(datos['precio'])
        cantidad  = int(datos['cantidad'])
        subtotal  = precio * cantidad
        total    += subtotal
        items.append({
            'prod_id':  prod_id,
            'nombre':   datos['nombre'],
            'precio':   precio,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'imagen':   datos.get('imagen'),
        })

    return render(request, 'catalogo/carrito.html', {
        'items': items,
        'total': total,
    })


def agregar_al_carrito(request, producto_id: int):
    """Agrega un producto al carrito o incrementa su cantidad."""
    if request.method != 'POST':
        return redirect('catalogo:catalogo')

    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito  = _obtener_carrito(request)

    clave    = str(producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    if clave in carrito:
        carrito[clave]['cantidad'] += cantidad
    else:
        carrito[clave] = {
            'nombre':   producto.nombre,
            'precio':   str(producto.precio),
            'cantidad': cantidad,
            'imagen':   producto.imagen.name if producto.imagen else None,
        }

    _guardar_carrito(request, carrito)
    messages.success(
        request,
        f'"{producto.nombre}" agregado al carrito.'
    )

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    return redirect(next_url or 'catalogo:catalogo')


def remover_del_carrito(request, producto_id: int):
    """Elimina un producto del carrito."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave   = str(producto_id)

    nombre = carrito.get(clave, {}).get('nombre', 'Producto')
    carrito.pop(clave, None)
    _guardar_carrito(request, carrito)

    messages.warning(request, f'"{nombre}" eliminado del carrito.')
    return redirect('catalogo:carrito')


def actualizar_cantidad(request, producto_id: int):
    """Actualiza la cantidad de un producto en el carrito."""
    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito  = _obtener_carrito(request)
    clave    = str(producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    if clave in carrito:
        if cantidad > 0:
            carrito[clave]['cantidad'] = cantidad
        else:
            carrito.pop(clave)

    _guardar_carrito(request, carrito)
    return redirect('catalogo:carrito')


def vaciar_carrito(request):
    """Elimina todos los productos del carrito."""
    if request.method == 'POST':
        _guardar_carrito(request, {})
        messages.info(request, 'Carrito vaciado.')
    return redirect('catalogo:carrito')


# ── CHECKOUT (W14 / W15) ───────────────────────────────────────────────────

@login_required
def checkout(request):
    carrito = _obtener_carrito(request)
    if not carrito:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('catalogo:catalogo')

    totales = calcular_totales(carrito)
    items = armar_items(carrito)

    if request.method == 'POST':
        cliente = obtener_o_crear_cliente(request.user)
        numero_pedido = generar_numero_pedido()

        # Se eliminaron 'subtotal' e 'iva' para coincidir con tu modelo Pedido
        pedido = Pedido.objects.create(
            cliente=cliente,
            numero_pedido=numero_pedido,
            total_pagado=totales['total'],
            estado='pendiente',
        )

        for prod_id, datos in carrito.items():
            producto = get_object_or_404(Producto, pk=int(prod_id))
            DetalleVenta.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=int(datos['cantidad']),
                precio_unitario=Decimal(datos['precio']),
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        monto_centavos = int(totales['total'] * 100)

        intent = stripe.PaymentIntent.create(
            amount=monto_centavos,
            currency='mxn',
            metadata={'pedido_id': str(pedido.id)}
        )

        return render(request, 'catalogo/checkout.html', {
            'carrito': carrito,
            'items': items,
            'totales': totales,
            'pedido': pedido,
            'client_secret': intent.client_secret,
            'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        })

    return render(request, 'catalogo/checkout.html', {
        'carrito': carrito,
        'items': items,
        'totales': totales,
        'client_secret': '',
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


def pago_exitoso(request, pedido_id: int):
    """Vista de confirmación post-pago exitoso."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    _guardar_carrito(request, {})
    messages.success(
        request,
        f'¡Pago exitoso! Tu pedido {pedido.numero_pedido} '
        f'está confirmado. Total: ${pedido.total_pagado}'
    )

    return render(request, 'catalogo/pago_exitoso.html', {
        'pedido': pedido,
    })


def pago_error(request):
    """Vista de error de pago."""
    return render(request, 'catalogo/pago_error.html')