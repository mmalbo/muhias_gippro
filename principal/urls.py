from django.urls import path, include
from . import views

urlpatterns = [
    # Ruta principal después del login
    path('', views.cargar_datos_principal, name='principal'),
    
    # Rutas de autenticación
    path('login/principal', views.LoginTemplateView.as_view(), name='login'),
    path('login/', views.loginPage, name='loginPage'),
    path('logout/', views.logoutUser, name='logoutUser'),

    # Rutas para diferentes secciones de la aplicación
    path('almacen/', include('nomencladores.almacen.urls'), name='almacen'),
    path('tipos_materia_prima/', include('materia_prima.tipo_materia_prima.urls'), name='tipos_materia_prima'),
    path('materia_prima/', include('materia_prima.urls'), name='materia_prima'),
    path('produccion/', include('produccion.urls'), name='produccion'),
    path('producto/', include('producto.urls'), name='producto'),
    path('tapa/', include('envase_embalaje.tapa.urls'), name='tapa'),
    path('tanque/', include('envase_embalaje.tanque.urls'), name='tanque'),
    path('tipo_envase_embalaje/', include('envase_embalaje.tipo_envase_embalaje.urls'), name='tipo_envase_embalaje'),
    path('pomo/', include('envase_embalaje.pomo.urls'), name='pomo'),
    path('caja/', include('envase_embalaje.caja.urls'), name='caja'),
    path('formato/', include('envase_embalaje.formato.urls'), name='formato'),
    path('envase_embalaje/', include('envase_embalaje.urls'), name='envase_embalaje'),
    path('planta/', include('nomencladores.planta.urls'), name='planta'),
    path('usuario/', include('usuario.urls'), name='usuario'),
    path('adquisiciones/', include('adquisiciones.urls'), name='adquisiciones'),
    path('insumos/', include('InsumosOtros.urls'), name='insumos'),
    path('utils/', include('utils.urls'), name='utils'),

    # Otras rutas pueden ser añadidas aquí
]