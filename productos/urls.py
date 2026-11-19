from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('',
         views.ProductoListView.as_view(),      name='lista'),
    path('<int:producto_id>/',
         views.ProductoDetailView.as_view(),    name='detalle'),
    path('nuevo/',
         views.ProductoCreateView.as_view(),    name='crear'),
    path('<int:producto_id>/editar/',
         views.ProductoUpdateView.as_view(),    name='editar'),
    path('<int:producto_id>/eliminar/',
         views.ProductoDeleteView.as_view(),    name='eliminar'),
    path('exportar-excel/',
         views.exportar_excel,                  name='exportar_excel'),
    # Historial de cambios — W21
    path('<int:producto_id>/historico/',
         views.HistoricoProductoView.as_view(), name='historico'),
]