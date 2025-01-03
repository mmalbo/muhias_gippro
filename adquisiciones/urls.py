from django.urls import path
from .views import (
    MateriaPrimaAdquisicionListView,
    MateriaPrimaAdquisicionDetailView,
    # MateriaPrimaAdquisicionCreateView,
    MateriaPrimaAdquisicionUpdateView,
    EnvaseAdquisicionListView,
    EnvaseAdquisicionDetailView,
    # EnvaseAdquisicionCreateView,
    EnvaseAdquisicionUpdateView,
    InsumosAdquisicionListView,
    InsumosAdquisicionDetailView,
    # InsumosAdquisicionCreateView,
    InsumosAdquisicionUpdateView,

)
from . import views
urlpatterns = [
    path('materia_prima_adquisicion/', MateriaPrimaAdquisicionListView.as_view(), name='materia_prima_adquisicion_list'),
    path('materia_prima_adquisicion/<uuid:pk>/', MateriaPrimaAdquisicionDetailView.as_view(), name='materia_prima_adquisicion_detail'),
    # path('materia_prima_adquisicion/create/', MateriaPrimaAdquisicionCreateView.as_view(), name='materia_prima_adquisicion_create'),
    path('materia_prima_adquisicion/create/', views.materiaAdquisicionCreateView, name='materia_prima_adquisicion_create'),
    path('materia_prima_adquisicion/nuevo/', views.materia_add, name='materia_adquisicion_add'),
    path('materia_prima_adquisicion/update/<uuid:pk>/', MateriaPrimaAdquisicionUpdateView.as_view(), name='materia_prima_adquisicion_update'),

    path('envase_adquisicion/', EnvaseAdquisicionListView.as_view(), name='envase_adquisicion_list'),
    path('envase_adquisicion/<uuid:pk>/', EnvaseAdquisicionDetailView.as_view(), name='envase_adquisicion_detail'),
    path('envase_adquisicion/create/', views.envaseAdquisicionCreateView, name='envase_adquisicion_create'),
    path('envase_adquisicion/nuevo/', views.envases_add, name='envase_adquisicion_add'),
    path('envase_adquisicion/update/<uuid:pk>/', EnvaseAdquisicionUpdateView.as_view(), name='envase_adquisicion_update'),

    path('insumos_adquisicion/', InsumosAdquisicionListView.as_view(), name='insumos_adquisicion_list'),
    path('insumos_adquisicion/<uuid:pk>/', InsumosAdquisicionDetailView.as_view(), name='insumos_adquisicion_detail'),
    # path('insumos_adquisicion/create/', InsumosAdquisicionCreateView.as_view(), name='insumos_adquisicion_create'),
    path('insumos_adquisicion/create/', views.insumosAdquisicionCreateView, name='insumos_adquisicion_create'),
    path('insumos_adquisicion/nuevo/', views.insumos_add, name='insumos_adquisicion_add'),
    path('insumos_adquisicion/update/<uuid:pk>/', InsumosAdquisicionUpdateView.as_view(), name='insumos_adquisicion_update'),
]