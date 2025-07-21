from django.urls import path
from .views import CompraWizard, MateriaPrimaDetalleView, compra_exitosa, EnvaseDetalleView, CompraEnvaseWizard

urlpatterns = [
     path('compras/nueva/', CompraWizard.as_view(), name='nueva_compra'),
     path('api/materias-primas/<uuid:pk>/', MateriaPrimaDetalleView.as_view(), name='materia_prima_detalle'),
     path('compras/nuevo-envase/', CompraEnvaseWizard.as_view(), name='nueva_compra_envase'),
     path('api/envases/<uuid:pk>/', EnvaseDetalleView.as_view(), name='envase_detalle'),
     path('compras/exito/', compra_exitosa, name='compra_exitosa'),
]
