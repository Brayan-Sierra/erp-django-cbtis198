# productos/admin.py
from django.contrib  import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(SimpleHistoryAdmin):
    """Admin de productos con preview de imagen e historial — W11 / W21 / W23."""

    list_display        = ['pk', 'imagen_preview', 'nombre', 'precio',
                           'stock', 'categoria', 'proveedor', 'activo']
    list_select_related = ('categoria', 'proveedor')
    search_fields       = ['nombre', 'categoria__nombre', 'proveedor__nombre']
    list_filter         = ['activo', 'categoria']
    list_editable       = ['precio', 'stock', 'activo']
    readonly_fields     = ['creado', 'imagen_preview_grande']
    date_hierarchy      = 'creado'
    ordering            = ['nombre']

    @admin.display(description='Imagen')
    def imagen_preview(self, obj: Producto) -> str:
        """Miniatura de la imagen en la lista del admin."""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;'
                'object-fit:cover;border-radius:6px;">',
                obj.imagen.url
            )
        return '—'

    @admin.display(description='Vista previa')
    def imagen_preview_grande(self, obj: Producto) -> str:
        """Imagen ampliada en el formulario de edición del admin."""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-height:200px;'
                'border-radius:8px;margin-top:.5rem;">',
                obj.imagen.url
            )
        return 'Sin imagen'