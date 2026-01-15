from django.urls import path
from . import views


urlpatterns = [
    path('listar/', views.listEnvaseEmbalaje, name='envase_embalaje_lista'),
    path('crear/', views.EnvaseEmbalajeCreateView.as_view(), name='envase_embalaje_crear'),
    path('eliminar/<uuid:pk>/', views.DeleteEnvaseEmbalajeView.as_view(), name='envase_embalaje_eliminar'),
    path('envase_embalaje/<uuid:pk>/', views.get_envase_embalaje, name='get_envase_embalaje'),
    path('importar/', views.CreateImportView.as_view(), name='importarEnvaseEmbalaje'),
    path('actualizar/<uuid:pk>/', views.UpdateEnvaseEmbalajeView.as_view(), name='envase_embalaje_editar'),
]