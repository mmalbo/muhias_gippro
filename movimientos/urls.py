from django.urls import path
from .views import *

urlpatterns = [
     path('recpendientes/', recepciones_pendientes_list, name='rec_pend_list'),
     path('solpendientes/', solicitudes_pendientes_list, name='solicitudes_pendientes'),
     path('recepcion/mp/<int:adq_id>/', recepcion_materia_prima , name='recepcion_mp'),
     path('recepcion/prod/<int:adq_id>/', recepcion_producto , name='recepcion_prod'),
     path('recepcion/env/<int:adq_id>/', recepcion_envase , name='recepcion_env'),
     path('recepcion/ins/<int:adq_id>/', recepcion_insumo , name='recepcion_ins'),
     path('entrada/mp/<uuid:pk>/', entrada_materia_prima , name='entrada_mp'),
     path('entrada/prod/<uuid:pk>/', entrada_producto , name='entrada_prod'),
     path('entrada/prod_prod/<uuid:pk>/', entrada_producto_produccion , name='entrada_prod_prod'),
     path('entrada/env/<uuid:pk>/', entrada_envase , name='entrada_env'),
     path('entrada/ins/<uuid:pk>/', entrada_insumo , name='entrada_ins'),
     path('salida_produccion/<uuid:prod_id>/', salida_produccion , name='salida_prod'),
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