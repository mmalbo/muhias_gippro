from django.urls import path
from . import views

app_name = 'fichas_costo'

urlpatterns = [
    # Listar
    path('', views.lista_fichas_costo, name='lista'),
    # path('', views.FichaCostoListView.as_view(), name='lista'),  # Versión con clase
    
    # Crear
    path('crear/', views.crear_ficha_costo, name='crear'),
    # path('crear/', views.FichaCostoCreateView.as_view(), name='crear'),  # Versión con clase
    
    # Detalle
    path('<uuid:pk>/', views.detalle_ficha_costo, name='detalle'),
    # path('<int:pk>/', views.FichaCostoDetailView.as_view(), name='detalle'),  # Versión con clase
    
    # Editar
    path('<uuid:pk>/editar/', views.editar_ficha_costo, name='editar'),
    # path('<int:pk>/editar/', views.FichaCostoUpdateView.as_view(), name='editar'),  # Versión con clase
    
    # Eliminar
    path('<uuid:pk>/eliminar/', views.eliminar_ficha_costo, name='eliminar'),
    # path('<int:pk>/eliminar/', views.FichaCostoDeleteView.as_view(), name='eliminar'),  # Versión con clase
]