# reportes/tasks.py
"""Tareas asíncronas de la app reportes — W20.

generar_exportacion_async: genera el archivo en background y notifica
                            al usuario por correo cuando está listo.
"""
import logging
from typing import TYPE_CHECKING

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives

if TYPE_CHECKING:
    from reportes.models import ExportacionReporte

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name='reportes.generar_exportacion_async',
)
def generar_exportacion_async(self, exportacion_id: int) -> dict:
    """Genera el archivo de exportación y notifica por correo.

    Reconstruye el queryset filtrado a partir de los parámetros
    guardados en ExportacionReporte.filtros, genera el Excel o PDF
    con las funciones reutilizables de reportes/exports.py, y
    guarda el resultado en el FileField del registro.

    Args:
        exportacion_id: ID del registro ExportacionReporte.

    Returns:
        dict con el estado del procesamiento.
    """
    from reportes.exports import generar_excel_ventas, generar_pdf_ventas
    from reportes.filters import VentaReporteFilter
    from reportes.models  import ExportacionReporte
    from ventas.models    import Venta

    try:
        exportacion = ExportacionReporte.objects.get(pk=exportacion_id)
    except ExportacionReporte.DoesNotExist:
        logger.error(
            f'[exportacion_async] Exportación {exportacion_id} no existe.'
        )
        return {'estado': 'error', 'razon': 'no encontrada'}

    # ── Reconstruir el mismo filtro aplicado por el usuario ────────────
    qs = (
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto')
        .order_by('-fecha')
    )
    filtro    = VentaReporteFilter(exportacion.filtros, queryset=qs)
    queryset  = filtro.qs.distinct()

    try:
        # ── Generar el archivo según el formato ─────────────────────────
        if exportacion.formato == 'excel':
            buffer = generar_excel_ventas(queryset)
            nombre = f'reporte_ventas_{exportacion.pk}.xlsx'
        else:
            buffer = generar_pdf_ventas(queryset)
            nombre = f'reporte_ventas_{exportacion.pk}.pdf'

        # ── Guardar en el FileField ──────────────────────────────────────
        exportacion.archivo.save(
            nombre, ContentFile(buffer.read()), save=False
        )
        exportacion.completado = True
        exportacion.save(update_fields=['archivo', 'completado'])

        logger.info(
            f'[exportacion_async] Exportación {exportacion.pk} '
            f'completada: {nombre} ({queryset.count()} filas).'
        )

        _enviar_correo_exportacion_lista(exportacion)

        return {'estado': 'ok', 'exportacion_id': exportacion_id}

    except Exception as exc:
        exportacion.error = str(exc)
        exportacion.save(update_fields=['error'])
        logger.error(
            f'[exportacion_async] Error al generar exportación '
            f'{exportacion_id}: {exc}'
        )
        raise self.retry(exc=exc, countdown=120)


def _enviar_correo_exportacion_lista(exportacion: 'ExportacionReporte') -> None:
    """Envía un correo con el enlace de descarga al solicitante.

    Args:
        exportacion: instancia de ExportacionReporte con archivo guardado.
    """
    # Las tareas Celery no tienen 'request', por lo que el dominio
    # debe construirse desde una constante de configuración.
    dominio = getattr(
        settings, 'SITE_DOMAIN', 'https://erp-django-cbtis198.onrender.com'
    )
    url_descarga = f'{dominio}{exportacion.archivo.url}'

    mensaje = EmailMultiAlternatives(
        subject    = f'Tu reporte de ventas está listo (#{exportacion.pk})',
        body       = (
            f'Hola,\n\n'
            f'Tu exportación de ventas en formato '
            f'{exportacion.get_formato_display()} está lista.\n\n'
            f'Descárgala aquí: {url_descarga}\n\n'
            f'Equipo ERP Django'
        ),
        from_email = settings.DEFAULT_FROM_EMAIL,
        to         = [exportacion.usuario.email],
    )

    try:
        mensaje.send()
        logger.info(
            f'[exportacion_async] Correo de descarga enviado a '
            f'{exportacion.usuario.email}.'
        )
    except Exception as exc:
        logger.error(
            f'[exportacion_async] Error al enviar correo de '
            f'exportación: {exc}'
        )