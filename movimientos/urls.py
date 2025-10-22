from django.urls import path
from .views import *

urlpatterns = [
     path('recepcion/mp/<int:adq_id>/', recepcion_materia_prima , name='recepcion_mp'),
     path('recepcion/env/<int:adq_id>/', recepcion_envase , name='recepcion_env'),
     path('recepcion/ins/<int:adq_id>/', recepcion_insumo , name='recepcion_ins'),
     path('lista/', movimiento_list, name='movimiento_list'),
     path('vale/<int:cons>/', generar_vale, name='generar_vale'),
     path('detalle/<int:cons>/', movimiento_detalle, name='movimiento_detalle'),
]