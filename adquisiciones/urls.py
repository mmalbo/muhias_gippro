from django.urls import path
from .views import CompraWizard, MateriaPrimaDetalleView, compra_exitosa

urlpatterns = [
     path('compras/nueva/', CompraWizard.as_view(), name='nueva_compra'),
     path('api/materias-primas/<uuid:pk>/', MateriaPrimaDetalleView.as_view(), name='materia_prima_detalle'),
     path('compras/exito/', compra_exitosa, name='compra_exitosa'),
]
