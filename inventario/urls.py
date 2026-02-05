from django.urls import path
from .views import ajuste_inv_mp, ajuste_inv_env, ajuste_inv_ins, ajuste_inv_prod

urlpatterns = [
     path('mp-update/<uuid:inv_mp>/', ajuste_inv_mp, name='ajuste_inv_mp'),
     path('ee-update/<uuid:inv_ee>/', ajuste_inv_env, name='ajuste_inv_ee'),
     path('ins-update/<uuid:inv_ins>/', ajuste_inv_ins, name='ajuste_inv_ins'),
     path('prod-update/<uuid:inv_prod>/', ajuste_inv_prod, name='ajuste_inv_prod'),
]