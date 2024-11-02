from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView, UpdateView, CreateView

from .forms import TipoMateriaPrimaForm
from .models import TipoMateriaPrima


class ListaTiposMateriaPrimaView(ListView):
    model = TipoMateriaPrima
    template_name = 'tipo_materia_prima/lista.html'
    context_object_name = 'tipos_materias_primas'


class CrearTipoMateriaPrimaView(CreateView):
    model = TipoMateriaPrima
    form_class = TipoMateriaPrimaForm
    template_name = 'tipo_materia_prima/form.html'
    success_url = reverse_lazy('tipo_materia_prima:lista')
    success_message = "Se ha creado correctamente el almacén."


class ActualizarTipoMateriaPrimaView(UpdateView):
    model = TipoMateriaPrima
    form_class = TipoMateriaPrimaForm
    template_name = 'tipo_materia_prima/form.html'
    success_url = reverse_lazy('tipo_materia_prima:lista')
    success_message = "Se ha modificado correctamente el almacén."


class EliminarTipoMateriaPrimaView(DeleteView):
    model = TipoMateriaPrima
    template_name = 'tipo_materia_prima/eliminar.html'
    success_url = '/tipos_materia_prima/'
