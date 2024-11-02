from django.urls import path
from .views import (
    CustomUserListView,
    CustomUserCreateView,
    CustomUserUpdateView,
    CustomUserDeleteView
)

urlpatterns = [
    path('usuario/', CustomUserListView.as_view(), name='customuser_list'),
    path('usuario/añadir/', CustomUserCreateView.as_view(), name='customuser_create'),
    path('usuario/<int:pk>/actualizar/', CustomUserUpdateView.as_view(), name='customuser_update'),
    path('usuario/<int:pk>/eliminar/', CustomUserDeleteView.as_view(), name='customuser_delete'),
]