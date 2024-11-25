from django.urls import path
from . import views


urlpatterns = [
    path('almacenes/', views.AlmacenListView.as_view(), name='almacen_lista'),
    path('almacenes/crear/', views.AlmacenCreateView.as_view(), name='almacen_crear'),
    path('almacenes/<uuid:pk>/editar/', views.AlmacenUpdateView.as_view(), name='almacen_editar'),
    path('almacenes/<uuid:pk>/eliminar/', views.AlmacenDeleteView.as_view(), name='almacen_eliminar'),
    path('almacenes/<uuid:pk>/', views.get_almacenes, name='get_almacenes'),
    path('importar/', views.CreateImportView.as_view(), name='importarAlmacenes'),
    path('importar/importar/', views.importar, name='importarA'),

]