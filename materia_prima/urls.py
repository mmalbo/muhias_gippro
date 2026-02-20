from django.urls import path
from . import views

app_name = 'materia_prima'

urlpatterns = [
    path('catalogo/', views.ListMateriaPrimaView.as_view(), name='list_materia_prima'),
    path('crear/', views.CreateMateriaPrimaView.as_view(), name='materia_prima_crear'),
    path('listar/', views.listMateriasPrimas, name='materia_prima_list'),
    path('actualizar/<uuid:pk>/', views.UpdateMateriaPrimaView.as_view(), name='materia_prima_actualizar'),
    path('eliminar/<uuid:pk>/', views.DeleteMateriaPrimaView.as_view(), name='materia_prima_eliminar'),
    path('materias_primas/<uuid:pk>/', views.get_materias_primas, name='get_materias_primas'),
    path('importar/', views.CreateImportView.as_view(), name='importarMateriasPrimas'),
    path('importar/importar/', views.importar, name='importarMP'),
    path('importar_costo/', views.CreateImportCostoView.as_view(), name='updateCostoMateriasPrimas'),
    path('importar/costo/', views.importarCosto, name='updateCosto'),

    path('categorias/', views.gestionar_tipos_MP, name='gestionar_tipos_categorias'),
    path('categorias/eliminar/<str:valor>/', views.eliminar_tipos_MP, name='eliminar_categoria'),
]
#path('listar/', views.ListMateriaPrimaView.as_view(), name='materia_prima_list'),