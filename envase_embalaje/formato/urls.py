from django.urls import path
from . import views

app_name = 'formato'

urlpatterns = [
    path('crear/', views.CreateFormatoView.as_view(), name='crear'),
    path('lista/', views.ListFormatoView.as_view(), name='listar'),
    path('actualizar/<uuid:pk>/', views.UpdateFormatoView.as_view(), name='actualizar'),
    path('eliminar/<uuid:pk>/', views.DeleteCapacidadView.as_view(), name='eliminar'),
]