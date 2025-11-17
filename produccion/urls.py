# urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import ( ProduccionListView, ProduccionDeleteView, CrearProduccionView, get_materias_primas_data,
                    iniciar_produccion, concluir_produccion, subir_pruebas_quimicas, descargar_pruebas_quimicas,
                    eliminar_pruebas_quimicas, cancelar_produccion, detalle_cancelacion )

urlpatterns = [
    path('', ProduccionListView.as_view(), name='produccion_list'),
    #path('<uuid:pk>/editar/', ProduccionUpdateView.as_view(), name='produccion_update'),
    path('<uuid:pk>/eliminar/', ProduccionDeleteView.as_view(), name='produccion_delete'),

    #Creación de nuevas producciones
    path('nueva/', CrearProduccionView.as_view(), name='crear_produccion'),
    path('api/materias-primas/', get_materias_primas_data, name='materias_primas_data'),
    
    #Iniciar produccion 
    path('<uuid:pk>/iniciar/', iniciar_produccion, name='iniciar_produccion'),
    #path('<uuid:pk>/iniciar/', CambiarEstadoProduccionView.as_view(), name='cambiar_produccion'),

    #Concluir producción
    path('produccion/<uuid:pk>/concluir/', concluir_produccion, name='concluir_produccion'),

    #Subir pruebas
    path('produccion/<uuid:pk>/pruebas/', subir_pruebas_quimicas, name='subir_pruebas'),
    path('produccion/<uuid:pk>/pruebas/descargar/', descargar_pruebas_quimicas, name='descargar_pruebas'),
    path('produccion/<uuid:pk>/pruebas/eliminar/', eliminar_pruebas_quimicas, name='eliminar_pruebas'),

    #Cancelación
    path('produccion/<uuid:pk>/cancelar/', cancelar_produccion, name='cancelar_produccion'),
    path('produccion/<uuid:pk>/cancelacion/detalle/', detalle_cancelacion, name='detalle_cancelacion'),
]

# Para servir archivos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)