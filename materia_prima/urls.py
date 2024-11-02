from django.urls import path
from . import views

app_name = 'materia_prima'

urlpatterns = [
    path('crear/', views.CreateMateriaPrimaView.as_view(), name='materia_prima_crear'),
    path('listar/', views.ListMateriaPrimaView.as_view(), name='materia_prima_list'),
    path('actualizar/<uuid:pk>/', views.UpdateMateriaPrimaView.as_view(), name='materia_prima_actualizar'),
    path('eliminar/<uuid:pk>/', views.DeleteMateriaPrimaView.as_view(), name='materia_prima_eliminar'),
    path('materias_primas/<uuid:pk>/', views.get_materias_primas, name='get_materias_primas'),
]
