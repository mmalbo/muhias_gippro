from django.urls import path
from .views import CompraWizard, MateriaPrimaDetalleView, compra_exitosa, EnvaseDetalleView, CompraEnvaseWizard, CompraInsumoWizard, InsumoDetalleView, list_mp_adquisiciones, list_env_adquisiciones, list_ins_adquisiciones, list_detalles_mp_adquisicion, list_detalles_env_adquisicion, list_detalles_ins_adquisicion, list_detalles_prod_adquisicion, list_prod_adquisiciones, ProductoDetalleView, CompraProductoWizard

urlpatterns = [
     path('compras/mp-list/', list_mp_adquisiciones, name='compras_mp_list'),
     path('compras/mplist/<int:id>/', list_detalles_mp_adquisicion, name='detalles_mp_list'),
     path('compras/nueva/', CompraWizard.as_view(), name='nueva_compra'),
     path('api/materias-primas/<uuid:pk>/', MateriaPrimaDetalleView.as_view(), name='materia_prima_detalle'),

     path('compras/env-list/', list_env_adquisiciones, name='compras_env_list'),
     path('compras/env-list/detalles/<int:id>/', list_detalles_env_adquisicion, name='detalles_env_list'),
     path('compras/nuevo-envase/', CompraEnvaseWizard.as_view(), name='nueva_compra_envase'),
     path('api/envases/<uuid:pk>/', EnvaseDetalleView.as_view(), name='envase_detalle'),
     
     path('compras/ins-list/', list_ins_adquisiciones, name='compras_ins_list'),
     path('compras/ins-list/detalles/<int:id>/', list_detalles_ins_adquisicion, name='detalles_ins_list'),
     path('compras/nuevo-insumo/', CompraInsumoWizard.as_view(), name='nueva_compra_insumo'),
     path('api/insumo/<uuid:pk>/', InsumoDetalleView.as_view(), name='insumo_detalle'),

     path('compras/prod-list/', list_prod_adquisiciones, name='compras_prod_list'),
     path('compras/prod-list/detalles/<int:id>/', list_detalles_prod_adquisicion, name='detalles_prod_list'),
     path('compras/nuevo-producto/', CompraProductoWizard.as_view(), name='nueva_compra_producto'),
     path('api/producto/<uuid:pk>/', ProductoDetalleView.as_view(), name='producto_detalle'),
     
     path('compras/exito/', compra_exitosa, name='compra_exitosa'),
]
