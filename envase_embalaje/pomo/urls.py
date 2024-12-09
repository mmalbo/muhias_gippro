from django.urls import path
from . import views

app_name = 'pomo'

urlpatterns = [
    path('crear/', views.CreatePomoView.as_view(), name='crear'),
    path('', views.ListPomoView.as_view(), name='listar'),
    path('actualizar/<uuid:pk>/', views.UpdatePomoView.as_view(), name='actualizar'),
    path('eliminar/<uuid:pk>/', views.DeletePomoView.as_view(), name='eliminar'),
    path('importar/', views.CreateImportView.as_view(), name='crearImportarPomo'),
    path('importar/importar/', views.importarPomo, name='importarPomo'),

]