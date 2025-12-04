from django.urls import path
from .views import *

urlpatterns = [
     path('recpendientes/', recepciones_pendientes_list, name='rec_pend_list'),
     path('solpendientes/', solicitudes_pendientes_list, name='solicitudes_pendientes'),
     path('recepcion/mp/<int:adq_id>/', recepcion_materia_prima , name='recepcion_mp'),
     path('salida_produccion/<uuid:prod_id>/', salida_produccion , name='salida_prod'),
     path('recepcion/env/<int:adq_id>/', recepcion_envase , name='recepcion_env'),
     path('recepcion/ins/<int:adq_id>/', recepcion_insumo , name='recepcion_ins'),
     path('solicitud_salida/', solicitud_salida, name='solicitudes_almacen'),
     path('lista/', movimiento_list, name='movimiento_list'),
     path('vale/<int:cons>/', generar_vale, name='generar_vale'),
     path('detalle/<int:cons>/', movimiento_detalle, name='movimiento_detalle'),
]