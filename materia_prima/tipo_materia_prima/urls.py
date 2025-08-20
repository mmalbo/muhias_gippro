from django.urls import path
from .views import (
    ListaTiposMateriaPrimaView,
    CrearTipoMateriaPrimaView,
    ActualizarTipoMateriaPrimaView,
    EliminarTipoMateriaPrimaView,
    CreateImportView,
    importarTipoMP,
)

app_name = 'tipo_materia_prima'

urlpatterns = [
    path('', ListaTiposMateriaPrimaView.as_view(), name='lista'),
    path('crear/', CrearTipoMateriaPrimaView.as_view(), name='crear'),
    path('<uuid:pk>/actualizar/', ActualizarTipoMateriaPrimaView.as_view(), name='actualizar'),
    path('<uuid:pk>/eliminar/', EliminarTipoMateriaPrimaView.as_view(), name='eliminar'),
    path('importar/', CreateImportView.as_view(), name='crearImportarTipoMP'),
    path('importar/importar/', importarTipoMP, name='importarTipoMP'),
]