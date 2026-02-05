from django.urls import path
from .views import *

urlpatterns = [
     path('recpendientes/', recepciones_pendientes_list, name='rec_pend_list'),
     path('solpendientes/', solicitudes_pendientes_list, name='solicitudes_pendientes'),
     path('recepcion/mp/<int:adq_id>/', recepcion_materia_prima , name='recepcion_mp'),
     path('salida_produccion/<uuid:prod_id>/', salida_produccion , name='salida_prod'),
     path('recepcion/env/<int:adq_id>/', recepcion_envase , name='recepcion_env'),
     path('recepcion/ins/<int:adq_id>/', recepcion_insumo , name='recepcion_ins'),
     path('lista/', movimiento_list, name='movimiento_list'),
     path('vale/<int:cons>/', generar_vale, name='generar_vale'),
     path('actualizar/<uuid:pk>/', vale_detalle, name='movimiento_update'),
     path('detalle/<int:cons>/', vale_detalle, name='movimiento_detalle'),
     path('salida/crear/', CrearSalidaView.as_view(), name='crear_salida'),
     path('salida/<uuid:pk>/confirmar/', confirmar_salida, name='confirmar_salida'),
     path('obtener-carrito/', obtener_carrito, name='obtener_carrito'),
     path('buscar-items/', buscar_items_almacen, name='buscar_items'),
     path('agregar-carrito/', agregar_item_carrito, name='agregar_carrito'),
     path('eliminar-carrito/', eliminar_item_carrito, name='eliminar_carrito'),
]
#UpdateMovimientoView.as_view()