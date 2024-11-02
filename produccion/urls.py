# urls.py
from django.urls import path
from .views import (
    ProduccionListView,
    ProduccionCreateView,
    ProduccionUpdateView,
    ProduccionDeleteView
)

urlpatterns = [
    path('', ProduccionListView.as_view(), name='produccion_list'),
    path('crear/', ProduccionCreateView.as_view(), name='produccion_create'),
    path('<uuid:pk>/editar/', ProduccionUpdateView.as_view(), name='produccion_update'),
    path('<uuid:pk>/eliminar/', ProduccionDeleteView.as_view(), name='produccion_delete'),
]