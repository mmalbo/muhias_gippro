from django.urls import path
from . import views

urlpatterns = [
    path('plantas/', views.ListPlantaView.as_view(), name='planta_lista'),
    path('plantas/crear/', views.CreatePlantaView.as_view(), name='planta_crear'),
    path('plantas/<uuid:pk>/editar/', views.UpdatePlantaView.as_view(), name='planta_editar'),
    path('plantas/<uuid:pk>/eliminar/', views.DeletePlantaView.as_view(), name='planta_eliminar'),
    path('importar/', views.CreateImportView.as_view(), name='importarPlantas'),
    path('importar/importar/', views.importar, name='importarP'),

]
