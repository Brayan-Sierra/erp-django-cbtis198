# reportes/views.py
"""Vistas del módulo de Dashboard y Reportes — W19 y W20."""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from clientes.models  import Cliente
from productos.models import Producto
from ventas.models    import DetalleVenta, Pedido, Venta

from .filters import VentaReporteFilter
from .models  import ExportacionReporte

CACHE_KEY_DASHBOARD = 'dashboard_kpis_v1'
CACHE_TTL_SEGUNDOS  = 300   # 5 minutos
UMBRAL_ASYNC        = 1000  # filas; por debajo se exporta en la misma petición


def _calcular_kpis() -> dict:
    """Calcula los 5 KPIs y los 3 datasets de gráficas del dashboard."""
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
        ventas_por_dia.append(float(total))

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
    """Dashboard principal con 5 KPIs y 3 gráficas Chart.js."""

    template_name = 'reportes/dashboard.html'

    def get_context_data(self, **kwargs) -> dict:
        """Construye el contexto con KPIs y datasets JSON para Chart.js."""
        ctx = super().get_context_data(**kwargs)

        kpis = cache.get_or_set(
            CACHE_KEY_DASHBOARD,
            _calcular_kpis,
            CACHE_TTL_SEGUNDOS
        )

        ctx.update(kpis)

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


class ReporteVentasView(LoginRequiredMixin, ListView):
    """Reporte de ventas filtrable por fecha, cliente y producto."""

    model               = Venta
    template_name       = 'reportes/reporte_ventas.html'
    context_object_name = 'ventas'
    paginate_by         = 20

    def get_queryset(self):
        """Aplica el filtro VentaReporteFilter sobre el queryset base."""
        qs = (
            Venta.objects
            .select_related('cliente')
            .prefetch_related('detalles__producto')
            .order_by('-fecha')
        )
        self.filtro = VentaReporteFilter(self.request.GET, queryset=qs)
        return self.filtro.qs.distinct()

    def get_context_data(self, **kwargs) -> dict:
        """Agrega el objeto filtro y el conteo total al contexto."""
        ctx = super().get_context_data(**kwargs)
        ctx['filtro']         = self.filtro
        ctx['total_filtrado'] = self.filtro.qs.distinct().count()
        return ctx


@login_required
def exportar_reporte(request):
    """Exporta el reporte de ventas filtrado a Excel o PDF."""
    from .exports import generar_excel_ventas, generar_pdf_ventas
    from .tasks   import generar_exportacion_async

    formato = request.GET.get('formato', 'excel')

    qs = (
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto')
        .order_by('-fecha')
    )
    filtro   = VentaReporteFilter(request.GET, queryset=qs)
    queryset = filtro.qs.distinct()
    total    = queryset.count()

    # ── Ruta asíncrona: volumen grande ──────────────────────────────────
    if total > UMBRAL_ASYNC:
        exportacion = ExportacionReporte.objects.create(
            usuario = request.user,
            formato = formato,
            filtros = request.GET.dict(),
        )
        generar_exportacion_async.delay(exportacion.pk)

        messages.info(
            request,
            f'Tu reporte tiene {total} registros. '
            f'Te enviaremos un correo con el enlace de descarga '
            f'cuando esté listo.'
        )
        return redirect(
            'reportes:exportacion_en_proceso',
            exportacion_id=exportacion.pk
        )

    # ── Ruta síncrona: volumen manejable ────────────────────────────────
    if formato == 'excel':
        buffer = generar_excel_ventas(queryset)
        response = HttpResponse(
            buffer.read(),
            content_type=(
                'application/vnd.openxmlformats-officedocument'
                '.spreadsheetml.sheet'
            )
        )
        response['Content-Disposition'] = (
            'attachment; filename="reporte_ventas.xlsx"'
        )
    else:
        buffer = generar_pdf_ventas(queryset)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="reporte_ventas.pdf"'
        )

    return response


@login_required
def exportacion_en_proceso(request, exportacion_id: int):
    """Página de espera mientras se genera la exportación asíncrona."""
    exportacion = get_object_or_404(
        ExportacionReporte, pk=exportacion_id, usuario=request.user
    )
    return render(request, 'reportes/exportacion_en_proceso.html', {
        'exportacion': exportacion,
    })