# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('catalogo/', ListInsumosView.as_view(), name='list_insumos'),
    path('listar/', listInsumos, name='insumos_list'),
    path('crear/', InsumoCreateView.as_view, name='insumo_crear'),
    path('eliminar/<uuid:pk>/', DeleteInsumoView.as_view, name='insumo_eliminar'),
    path('insumo/<uuid:pk>/', get_insumo, name='get_insumo'),
    path('importar/', CreateImportView.as_view, name='importar_insumos'),  # Ruta para ver detalles
    path('actualizar/<uuid:pk>/', UpdateInsumosView.as_view, name='insumos_editar'),  # Ruta para ver detalles
]