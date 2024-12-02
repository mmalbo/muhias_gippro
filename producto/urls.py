from django.urls import path
from . import views

urlpatterns = [
    path('producto/', views.ListaProductoView.as_view(), name='producto_list'),
    path('producto/crear/', views.CrearProductoView.as_view(), name='crear_producto'),
    path('producto/<uuid:pk>/actualizar/', views.ActualizarProductoView.as_view(),
         name='actualizar_producto'),
    path('producto/<uuid:pk>/eliminar/', views.EliminarProductoView.as_view(),
         name='eliminar_producto'),
    # path('producto/<uuid:pk>/detalle/', views.DetalleProductoView.as_view(), name='detalle_producto'),
    path('importar/', views.CreateImportView.as_view(), name='importarProducto'),
    path('importar/importar/', views.importar, name='importarProd'),

]
