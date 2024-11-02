from django.urls import path
from . import views


urlpatterns = [
    path('envase_embalaje/', views.EnvaseEmbalajeListView.as_view(), name='envase_embalaje_lista'),
    path('envase_embalaje/crear/', views.EnvaseEmbalajeCreateView.as_view(), name='envase_embalaje_crear'),
    path('envase_embalaje/<uuid:pk>/editar/', views.EnvaseEmbalajeUpdateView.as_view(), name='envase_embalaje_editar'),
    path('envase_embalaje/<uuid:pk>/eliminar/', views.EnvaseEmbalajeDeleteView.as_view(), name='envase_embalaje_eliminar'),
]