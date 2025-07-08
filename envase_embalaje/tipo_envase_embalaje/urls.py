from django.urls import path
from . import views

urlpatterns = [
    # TipoEnvaseEmbalaje
    path('', views.TipoEnvaseEmbalajeListView.as_view(), name='tipo_envase_embalaje_list'),
]