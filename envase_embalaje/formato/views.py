from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from envase_embalaje.formato.forms import FormatoForm
from envase_embalaje.formato.models import Formato


# Create your views here.
class CreateFormatoView(CreateView):
    model = Formato
    form_class = FormatoForm
    template_name = 'capacidad/capacidad_form.html'
    success_url = '/formato/lista/'
    success_message = "Se ha creado correctamente la capacidad."


class ListFormatoView(ListView):
    model = Formato
    template_name = 'capacidad/capacidad_list.html'
    context_object_name = 'capacidades'


class UpdateFormatoView(UpdateView):
    model = Formato
    form_class = FormatoForm
    template_name = 'capacidad/capacidad_form.html'
    success_url = '/formato/lista/'


class DeleteCapacidadView(DeleteView):
    model = Formato
    template_name = 'capacidad/capacidad_confirm_delete.html'
    success_url = '/formato/lista/'
