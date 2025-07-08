from django.urls import path

#from . import views
from .views import FORMS, crear_adquisicion, adquisicion_detalle, AdquisicionWizard, MateriaPrimaAdquisicionListView, wizard_adquisicion, wizard_adquisicion
"""AdquisicionWizard, MateriaPrimaAdquisicionDetailView, MateriaPrimaAdquisicionWizard, \
    MateriaPrimaAdquisicionUpdateView , EnvaseAdquisicionListView, EnvaseAdquisicionDetailView, EnvaseAdquisicionUpdateView, InsumosAdquisicionListView, InsumosAdquisicionDetailView, InsumosAdquisicionUpdateView"""

urlpatterns = [
    path('materia_prima_adquisicion/', MateriaPrimaAdquisicionListView.as_view(), name='materia_prima_adquisicion_list'),
    #path('materia_prima_adquisicion/<uuid:pk>/', MateriaPrimaAdquisicionDetailView.as_view(), name='materia_prima_adquisicion_detail'),
    # path('materia_prima_adquisicion/create/', MateriaPrimaAdquisicionCreateView.as_view(), name='materia_prima_adquisicion_create'),
    #path('materia-prima/nueva/', AdquisicionWizard.as_view(), name='nueva_materia_prima_adquisicion'),
    #path('materia-prima/nueva/', AdquisicionWizard.as_view(FORMS), name='nueva_materia_prima_adquisicion'),
    path('adquisicion/', wizard_adquisicion, name='wizard_adquisicion'),
    path('adquisicion/paso/<int:step>/', wizard_adquisicion, name='wizard_adquisicion_step'),
    path('adquisiciones/', adquisicion_detalle, name='lista_adquisiciones'),
    #path('adquisicion/<int:pk>/', views.adquisicion_detalle, name='adquisicion_detalle'),
    #path('materia_prima_adquisicion/nuevo/', views.materia_add, name='materia_adquisicion_add'),
    #path('materia_prima_adquisicion/update/<uuid:pk>/', MateriaPrimaAdquisicionUpdateView.as_view(), name='materia_prima_adquisicion_update'),

    
]
