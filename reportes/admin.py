# reportes/admin.py
"""Configuración del panel admin para reportes — W20."""
from django.contrib import admin

from .models import ExportacionReporte


@admin.register(ExportacionReporte)
class ExportacionReporteAdmin(admin.ModelAdmin):
    """Admin de exportaciones — útil para depurar tareas fallidas."""

    list_display    = ['pk', 'usuario', 'formato', 'completado', 'creado']
    list_filter     = ['formato', 'completado']
    readonly_fields = ['creado', 'filtros']
    search_fields   = ['usuario__username']