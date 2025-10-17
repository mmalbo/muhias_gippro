# urls.py
from django.urls import path
from .views import ProduccionListView, ProduccionUpdateView, ProduccionDeleteView, CrearProduccionView, get_materias_primas_data

urlpatterns = [
    path('', ProduccionListView.as_view(), name='produccion_list'),
    #path('crear/', ProduccionCreateView.as_view(), name='produccion_create'),
    path('<uuid:pk>/editar/', ProduccionUpdateView.as_view(), name='produccion_update'),
    path('<uuid:pk>/eliminar/', ProduccionDeleteView.as_view(), name='produccion_delete'),

    path('nueva/', CrearProduccionView.as_view(), name='crear_produccion'),
    path('api/materias-primas/', get_materias_primas_data, name='materias_primas_data'),
]