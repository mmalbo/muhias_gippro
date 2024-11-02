from django.urls import path
from . import views

app_name = 'tanque'

urlpatterns = [
    path('crear/', views.CreateTanqueView.as_view(), name='crear'),
    path('', views.ListTanqueView.as_view(), name='listar'),
    path('actualizar/<uuid:pk>/', views.UpdateTanqueView.as_view(), name='actualizar'),
    path('eliminar/<uuid:pk>/', views.DeleteTanqueView.as_view(), name='eliminar'),
]