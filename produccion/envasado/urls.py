# urls.py
from django.urls import path
from . import views

app_name = 'envasado'

urlpatterns = [
    path('solicitudes/', views.lista_solicitudes_envasado, name='lista_solicitudes'),
    path('solicitudes/nueva/', views.SolicitudEnvasadoCreateView.as_view(), name='crear_solicitud'),
    path('solicitudes/<int:pk>/', views.detalle_solicitud_envasado, name='detalle_solicitud'),
    path('solicitudes/<int:pk>/iniciar/', views.iniciar_envasado, name='iniciar_envasado'),
    path('solicitudes/<int:solicitud_pk>/registrar-lote/', views.registrar_lote_envasado, name='registrar_lote'),
]