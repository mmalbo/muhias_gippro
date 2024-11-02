from django.urls import path
from .views import ColorListView

urlpatterns = [
    path('listar/', ColorListView.as_view(), name='color-list'),
]