# reportes/models.py
"""Modelos de la app reportes — W20.

ExportacionReporte rastrea las exportaciones generadas de forma
asíncrona (más de 1000 filas), permitiendo reconstruir el filtro
original en la tarea Celery y notificar al usuario por correo
cuando el archivo esté listo.
"""
from django.conf import settings
from django.db import models


class ExportacionReporte(models.Model):
    """Registro de una exportación de reporte generada en background.

    Atributos:
        usuario:    quién solicitó la exportación.
        formato:    'excel' o 'pdf'.
        filtros:    copia de los parámetros GET aplicados (para
                    reconstruir el mismo queryset en la tarea async).
        archivo:    el archivo generado (None hasta que termine).
        completado: True cuando la tarea terminó exitosamente.
        error:      mensaje de error si la generación falló.
    """

    FORMATO_CHOICES = [
        ('excel', 'Excel (.xlsx)'),
        ('pdf',   'PDF'),
    ]

    usuario    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exportaciones',
        verbose_name='Usuario solicitante',
    )
    formato    = models.CharField(
        max_length=10, choices=FORMATO_CHOICES, verbose_name='Formato'
    )
    filtros    = models.JSONField(
        default=dict, blank=True, verbose_name='Filtros aplicados'
    )
    archivo    = models.FileField(
        upload_to='exportaciones/', null=True, blank=True,
        verbose_name='Archivo generado'
    )
    completado = models.BooleanField(
        default=False, verbose_name='Completado'
    )
    error      = models.TextField(
        blank=True, verbose_name='Mensaje de error'
    )
    creado     = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de solicitud'
    )

    class Meta:
        verbose_name        = 'Exportación de reporte'
        verbose_name_plural  = 'Exportaciones de reportes'
        ordering             = ['-creado']

    def __str__(self) -> str:
        estado = 'completada' if self.completado else 'pendiente'
        return f'Exportación {self.get_formato_display()} #{self.pk} ({estado})'