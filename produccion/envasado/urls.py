# urls.py
from django.urls import path
from . import views

app_name = 'envasado'

urlpatterns = [
    path('solicitudes/', views.lista_solicitudes_envasado, name='lista_solicitudes'),
    path('solicitudes/nueva/', views.SolicitudEnvasadoCreateView.as_view(), name='crear_solicitud'),
    path('solicitudes/<uuid:pk>/', views.detalle_solicitud_envasado, name='detalle_solicitud_envasado'),
    path('solicitudes/<uuid:pk>/iniciar/', views.iniciar_envasado, name='iniciar_envasado'),
    path('solicitudes/<uuid:pk>/concluir/', views.concluir_envasado, name='concluir_envasado'),
    path('solicitudes/<uuid:pk>/cancelar/', views.cancelar_solicitud, name='cancelar_solicitud'),
    #path('solicitudes/<uuid:pk>/registrar-lote/', views.registrar_lote_envasado, name='registrar_lote_envasado'),

    # APIs AJAX - ¡Estas URLs son necesarias!
    path('api/detalle-lote/', views.obtener_detalle_lote, name='detalle_lote'),
    path('api/detalle-envase/', views.obtener_detalle_envase, name='detalle_envase'),
    path('api/detalle-insumo/', views.obtener_detalle_insumo, name='detalle_insumo'),
]