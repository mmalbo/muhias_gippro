from django.urls import path
from . import views

app_name = 'tapa'

urlpatterns = [
    path('crear/', views.CreateTapaView.as_view(), name='crear'),
    path('', views.ListTapaView.as_view(), name='listar'),
    path('actualizar/<uuid:pk>/', views.UpdateTapaView.as_view(), name='actualizar'),
    path('eliminar/<uuid:pk>/', views.DeleteTapaView.as_view(), name='eliminar'),
    path('importar/', views.CreateImportView.as_view(), name='crearImportarTapa'),
    path('importar/importar/', views.importarTapa, name='importarTapa'),
]
