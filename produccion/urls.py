# urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import ( ProduccionListView, ProduccionDeleteView, CrearProduccionView, get_materias_primas_data,
                    iniciar_produccion, concluir_produccion, subir_pruebas_quimicas, descargar_pruebas_quimicas,
                    eliminar_pruebas_quimicas, cancelar_produccion, detalle_cancelacion, agita_produccion, 
                    lista_parametros, crear_parametro, editar_parametro, detalle_parametro, crear_prueba_quimica,
                    detalle_prueba_quimica, agregar_parametros_prueba, editar_parametro_prueba, eliminar_parametro_prueba,
                    calcular_resultados_prueba, )

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

    #Iniciar produccion 
    path('<uuid:pk>/avance/', agita_produccion, name='agita_produccion'),

    #Concluir producción
    path('<uuid:pk>/concluir/', concluir_produccion, name='concluir_produccion'),

    #Crear pruebas
    path('<uuid:pk>/reg_prueba/', crear_prueba_quimica, name='crear_prueba_quimica'),
    path('<uuid:pk>/det_prueba/', detalle_prueba_quimica, name='detalle_prueba_quimica'),

    # Gestión de parámetros de una prueba
    path('prueba-quimica/<uuid:prueba_id>/agregar-parametros/', agregar_parametros_prueba, 
         name='agregar_parametros_prueba'),

     # Para editar DETALLE de prueba química (valor medido)
    #path('detalle-prueba-quimica/<uuid:detalle_id>/editar/', views.editar_detalle_prueba_quimica, name='editar_detalle_prueba_quimica'),
    
    # Para eliminar DETALLE de prueba química
    #path('detalle-prueba-quimica/<uuid:detalle_id>/eliminar/', views.eliminar_detalle_prueba_quimica, name='eliminar_detalle_prueba_quimica'),

    path('parametro-prueba/<uuid:pk>/editar/', editar_parametro_prueba, 
         name='editar_parametro_prueba'),
    
    path('parametro-prueba/<uuid:pk>/eliminar/', eliminar_parametro_prueba, 
         name='eliminar_parametro_prueba'),
    
    path('prueba-quimica/<uuid:pk>/calcular-resultados/', calcular_resultados_prueba, 
         name='calcular_resultados_prueba'),
    
    #path('prueba-quimica/<uuid:pk>/concluir/', concluir_prueba_quimica, name='concluir_prueba_quimica'),
    
    #path('prueba-quimica/<uuid:pk>/estado/<str:estado>/', cambiar_estado_prueba, name='cambiar_estado_prueba'),
    
    #Subir pruebas
    path('produccion/<uuid:pk>/pruebas/', subir_pruebas_quimicas, name='subir_pruebas'),
    path('produccion/<uuid:pk>/pruebas/descargar/', descargar_pruebas_quimicas, name='descargar_pruebas'),
    path('produccion/<uuid:pk>/pruebas/eliminar/', eliminar_pruebas_quimicas, name='eliminar_pruebas'),

    #Gestionar pruebas químicas
    path('parametros/', lista_parametros, name='parametros_lista'),
    path('parametros/crear/', crear_parametro, name='crear_parametro'),
    path('parametros/<uuid:parametro_id>/editar/', editar_parametro, name='editar_parametro'),
    path('parametros/<uuid:parametro_id>/', detalle_parametro, name='detalle_parametro'),

    #Cancelación
    path('produccion/<uuid:pk>/cancelar/', cancelar_produccion, name='cancelar_produccion'),
    path('produccion/<uuid:pk>/cancelacion/detalle/', detalle_cancelacion, name='detalle_cancelacion'),
]

# Para servir archivos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)