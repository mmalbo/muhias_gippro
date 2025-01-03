# urls.py
from django.urls import path
from .views import (
    insumos_list,
    insumos_create,
    insumos_update,
    insumos_delete,
    insumos_detail
)

urlpatterns = [
    path('', insumos_list, name='insumos_list'),
    path('create/', insumos_create, name='insumos_create'),
    path('update/<uuid:pk>/', insumos_update, name='insumos_update'),
    path('delete/<uuid:pk>/', insumos_delete, name='insumos_delete'),
    path('detail/<uuid:pk>/', insumos_detail, name='insumos_detail'),  # Ruta para ver detalles
]