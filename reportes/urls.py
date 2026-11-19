# reportes/urls.py
"""URLs de la app reportes — W20."""
from django.urls import path

from . import views

app_name = 'reportes'

urlpatterns = [
    # Dashboard (W19) — mantiene name='inicio' por compatibilidad navbar
    path('',
         views.DashboardView.as_view(),
         name='inicio'),

    # Reporte filtrable (W20)
    path('ventas/',
         views.ReporteVentasView.as_view(),
         name='reporte_ventas'),

    # Exportación
    path('exportar/',
         views.exportar_reporte,
         name='exportar'),
    path('exportacion/<int:exportacion_id>/',
         views.exportacion_en_proceso,
         name='exportacion_en_proceso'),
]