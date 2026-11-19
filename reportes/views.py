# reportes/views.py
"""Vistas del módulo de Dashboard y Reportes — W19.

DashboardView calcula 5 KPIs y 3 datasets de gráficas, cacheando
el resultado en Redis durante 5 minutos para evitar recalcular
en cada petición.
"""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from clientes.models   import Cliente
from productos.models  import Producto
from ventas.models     import DetalleVenta, Pedido

CACHE_KEY_DASHBOARD = 'dashboard_kpis_v1'
CACHE_TTL_SEGUNDOS  = 300   # 5 minutos


def _calcular_kpis() -> dict:
    """Calcula los 5 KPIs y los 3 datasets de gráficas del dashboard.

    Todas las agregaciones usan SQL (aggregate/annotate), no Python,
    para minimizar el tiempo de cómputo. Esta función es costosa
    y por eso se invoca a través de cache.get_or_set().

    Returns:
        dict serializable con KPIs y datasets para Chart.js.
    """
    hoy          = timezone.localdate()
    inicio_mes   = hoy.replace(day=1)
    hace_7_dias  = hoy - timedelta(days=6)

    # ── KPI 1: Ventas del día ───────────────────────────────────────────
    ventas_dia_total = Pedido.objects.filter(
        fecha_pedido__date=hoy, estado='pagado'
    ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')

    # ── KPI 2: Clientes nuevos hoy ───────────────────────────────────────
    clientes_nuevos = Cliente.objects.filter(creado__date=hoy).count()

    # ── KPI 3: Stock crítico ────────────────────────────────────────────
    stock_critico = Producto.objects.filter(
        activo=True, stock__lt=5
    ).count()

    # ── KPI 4: Pedidos pendientes ───────────────────────────────────────
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()

    # ── KPI 5: Revenue mensual ──────────────────────────────────────────
    revenue_mensual = Pedido.objects.filter(
        fecha_pedido__date__gte=inicio_mes, estado='pagado'
    ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')

    # ── Dataset 1: Ventas de los últimos 7 días (gráfica de línea) ──────
    labels_dias    = []
    ventas_por_dia = []
    for i in range(7):
        dia   = hace_7_dias + timedelta(days=i)
        total = Pedido.objects.filter(
            fecha_pedido__date=dia, estado='pagado'
        ).aggregate(total=Sum('total_pagado'))['total'] or Decimal('0.00')
        labels_dias.append(dia.strftime('%d/%m'))
        ventas_por_dia.append(float(total))   # float: Chart.js no usa Decimal

    # ── Dataset 2: Top 5 productos por ingreso histórico (barras) ───────
    expr_ingreso = ExpressionWrapper(
        F('cantidad') * F('precio_unitario'),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
    top_productos = list(
        DetalleVenta.objects
        .values(nombre=F('producto__nombre'))
        .annotate(ingreso=Sum(expr_ingreso))
        .order_by('-ingreso')[:5]
    )
    labels_productos  = [p['nombre'] for p in top_productos]
    valores_productos = [float(p['ingreso'] or 0) for p in top_productos]

    # ── Dataset 3: Ventas por categoría (dona) ───────────────────────────
    ventas_categoria = list(
        DetalleVenta.objects
        .values(categoria=F('producto__categoria__nombre'))
        .annotate(ingreso=Sum(expr_ingreso))
        .order_by('-ingreso')
    )
    labels_categorias  = [c['categoria'] for c in ventas_categoria]
    valores_categorias = [float(c['ingreso'] or 0) for c in ventas_categoria]

    return {
        'ventas_dia_total':    f'{ventas_dia_total:.2f}',
        'clientes_nuevos':     clientes_nuevos,
        'stock_critico':       stock_critico,
        'pedidos_pendientes':  pedidos_pendientes,
        'revenue_mensual':     f'{revenue_mensual:.2f}',
        'labels_dias':         labels_dias,
        'ventas_por_dia':      ventas_por_dia,
        'labels_productos':    labels_productos,
        'valores_productos':   valores_productos,
        'labels_categorias':   labels_categorias,
        'valores_categorias':  valores_categorias,
        'calculado_en':        timezone.now().isoformat(),
    }


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal con 5 KPIs y 3 gráficas Chart.js.

    Los datos se calculan con _calcular_kpis() y se cachean en Redis
    durante 5 minutos. Las peticiones subsecuentes dentro de esa
    ventana no ejecutan ninguna consulta SQL — solo leen de Redis.
    """

    template_name = 'reportes/dashboard.html'

    def get_context_data(self, **kwargs) -> dict:
        """Construye el contexto con KPIs y datasets JSON para Chart.js."""
        ctx = super().get_context_data(**kwargs)

        # cache.get_or_set: si la key existe y no expiró, NO ejecuta
        # _calcular_kpis(); si no existe o expiró, la ejecuta y guarda.
        kpis = cache.get_or_set(
            CACHE_KEY_DASHBOARD,
            _calcular_kpis,
            CACHE_TTL_SEGUNDOS
        )

        ctx.update(kpis)

        # Pre-serializar los datasets a JSON para inyectarlos en <script>
        ctx['chart_dias_json'] = json.dumps({
            'labels': kpis['labels_dias'],
            'data':   kpis['ventas_por_dia'],
        })
        ctx['chart_productos_json'] = json.dumps({
            'labels': kpis['labels_productos'],
            'data':   kpis['valores_productos'],
        })
        ctx['chart_categorias_json'] = json.dumps({
            'labels': kpis['labels_categorias'],
            'data':   kpis['valores_categorias'],
        })
        ctx['cache_ttl_minutos'] = CACHE_TTL_SEGUNDOS // 60

        return ctx