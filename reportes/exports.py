# reportes/exports.py
"""Funciones de generación de reportes — W20.

Reutilizadas tanto por la vista síncrona (exportar_reporte)
como por la tarea asíncrona (generar_exportacion_async),
evitando duplicar la lógica de construcción de Excel/PDF.
"""
import io
from decimal import Decimal

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill


def generar_excel_ventas(queryset) -> io.BytesIO:
    """Genera un archivo Excel con el listado de ventas dado.

    Args:
        queryset: QuerySet de Venta (ya filtrado).

    Returns:
        io.BytesIO con el contenido del archivo .xlsx, listo para leer.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Reporte de Ventas'

    # ── Estilos Fable 5 AzulERP ─────────────────────────────────────────
    encabezado_font  = Font(bold=True, color='FFFFFF', size=11)
    encabezado_fill  = PatternFill('solid', fgColor='0A2342')
    encabezado_align = Alignment(horizontal='center', vertical='center')

    columnas = [
        ('#',          8),
        ('Cliente',    32),
        ('Fecha',      20),
        ('Productos',  40),
        ('Total ($)',  14),
    ]
    for idx, (titulo, ancho) in enumerate(columnas, start=1):
        celda = ws.cell(row=1, column=idx, value=titulo)
        celda.font      = encabezado_font
        celda.fill      = encabezado_fill
        celda.alignment = encabezado_align
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(idx)
        ].width = ancho
    ws.row_dimensions[1].height = 22

    # ── Filas de datos ────────────────────────────────────────────────
    fila = 2
    for venta in queryset:
        productos_str = ', '.join(
            d.producto.nombre for d in venta.detalles.all()
        )
        ws.cell(row=fila, column=1, value=venta.pk)
        ws.cell(row=fila, column=2, value=venta.cliente.nombre)
        ws.cell(row=fila, column=3, value=venta.fecha.strftime('%d/%m/%Y %H:%M'))
        ws.cell(row=fila, column=4, value=productos_str)
        celda_total = ws.cell(row=fila, column=5, value=float(venta.total))
        celda_total.alignment = Alignment(horizontal='right')
        fila += 1

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def generar_pdf_ventas(queryset, contexto_extra: dict | None = None) -> io.BytesIO:
    """Genera un archivo PDF con el listado de ventas dado.

    Args:
        queryset:        QuerySet de Venta (ya filtrado).
        contexto_extra:  variables adicionales para el template.

    Returns:
        io.BytesIO con el contenido del archivo .pdf.
    """
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string

    from configuracion.models import ConfiguracionERP

    ventas = list(queryset)
    total_general = sum(
        (v.total for v in ventas), Decimal('0.00')
    )

    contexto = {
        'ventas':        ventas,
        'config':        ConfiguracionERP.get_instance(),
        'total_general': total_general,
    }
    if contexto_extra:
        contexto.update(contexto_extra)

    html_string = render_to_string(
        'reportes/reporte_ventas_pdf.html', contexto
    )

    buffer    = io.BytesIO()
    resultado = pisa.CreatePDF(src=html_string, dest=buffer)

    if resultado.err:
        raise RuntimeError(f'Error al generar PDF: {resultado.err}')

    buffer.seek(0)
    return buffer