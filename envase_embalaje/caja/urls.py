from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('crear/', views.CreateCajaView.as_view(), name='crear'),
    path('', views.ListCajaView.as_view(), name='listar'),
    path('actualizar/<uuid:pk>/', views.UpdateCajaView.as_view(), name='actualizar'),
    path('eliminar/<uuid:pk>/', views.DeleteCajaView.as_view(), name='eliminar'),
]