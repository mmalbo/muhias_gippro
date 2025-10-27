# urls.py
from django.urls import path
from .views import ProduccionListView, ProduccionDeleteView, CrearProduccionView, get_materias_primas_data, CambiarEstadoProduccionView, iniciar_produccion,concluir_produccion

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

    #Concluir producción
]