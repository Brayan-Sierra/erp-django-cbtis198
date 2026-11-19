# reportes/urls.py
"""URLs de la app reportes — W19."""
from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='inicio'),
]