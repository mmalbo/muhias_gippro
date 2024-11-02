from django.urls import path, include

from . import views
from django.contrib.auth import views as auth_views

# from expediente.views import *

urlpatterns = [
    path('', views.LoginTemplateView.as_view(), name='login'),
    # path('principal/', views.PrincipalTemplateView.as_view(), name='index'),
    # path('login/', views.loginPage, name='loginPage'),
    path('principal/', views.cargar_datos_principal, name='cargar_datos_principal'),
    path('login/', views.loginPage, name='loginPage'),
    path('logout/', views.logoutUser, name='logoutUser'),
    # path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('almacen/', include('nomencladores.almacen.urls'), name='almacen'),
    path('tipos_materia_prima/', include('materia_prima.tipo_materia_prima.urls'), name='tipos_materia_prima'),
    path('materia_prima/', include('materia_prima.urls'), name='materia_prima'),
    path('produccion/', include('produccion.urls'), name='produccion'),
    path('producto/', include('producto.urls'), name='producto'),
    # path('producto_final/', include('producto_final.urls'), name='producto_final'),
    path('tapa/', include('envase_embalaje.tapa.urls'), name='tapa'),
    path('tanque/', include('envase_embalaje.tanque.urls'), name='tanque'),
    path('pomo/', include('envase_embalaje.pomo.urls'), name='pomo'),
    path('caja/', include('envase_embalaje.caja.urls'), name='caja'),
    path('formato/', include('envase_embalaje.formato.urls'), name='formato'),
    path('envase_embalaje/', include('envase_embalaje.urls'), name='envase_embalaje'),
    path('planta/', include('nomencladores.planta.urls'), name='planta'),
    path('usuario/', include('usuario.urls'), name='usuario'),
    # path('materia_prima_almacen/', include('materia_prima_almacen.urls'), name='materia_prima_almacen'),
    # path('materiasPrimas/', include('materia_prima.ur'), name='logoutUser'),

    # Resto de las URLs de la aplicación de gestión
]
