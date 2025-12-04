from django.urls import path
from .views import ajuste_inv_mp

urlpatterns = [
     path('mp-update/<uuid:inv_mp>/', ajuste_inv_mp, name='ajuste_inv_mp'),
]