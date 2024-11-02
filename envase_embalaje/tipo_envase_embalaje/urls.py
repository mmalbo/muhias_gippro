from django.urls import path
from . import views

urlpatterns = [
    # TipoEnvaseEmbalaje
    path('', views.TipoEnvaseEmbalajeLista.as_view(), name='tipo_envase_embalaje_list'),
    path('tipos_envase_embalaje/crear/', views.TipoEnvaseEmbalajeCrear.as_view(), name='tipo_envase_embalaje_create'),
    path('tipos_envase_embalaje/<int:pk>/editar/', views.TipoEnvaseEmbalajeActualizar.as_view(), name='tipo_envase_embalaje_update'),
    path('tipos_envase_embalaje/<int:pk>/eliminar/', views.TipoEnvaseEmbalajeEliminar.as_view(), name='tipo_envase_embalaje_delete'),
]