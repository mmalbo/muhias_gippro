from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Producto
from .forms import ProductoForm


class ListaProductoView(ListView):
    model = Producto
    template_name = 'producto_final/lista_producto_final.html'
    context_object_name = 'productos_finales'


class CrearProductoView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_final/form.html'
    success_url = reverse_lazy('producto_final_list')


class ActualizarProductoView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_final/form.html'
    success_url = reverse_lazy('producto_final_list')


class EliminarProductoView(DeleteView):
    model = Producto
    template_name = 'producto_final/eliminar_producto_final.html'
    success_url = reverse_lazy('producto_final_list')


class DetalleProductoView(DetailView):
    model = Producto
    template_name = 'producto_final/detalle_producto_final.html'
