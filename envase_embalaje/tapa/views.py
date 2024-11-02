from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from envase_embalaje.tapa.forms import TapaForm
from envase_embalaje.tapa.models import Tapa


# Create your views here.
class CreateTapaView(CreateView):
    model = Tapa
    form_class = TapaForm
    template_name = 'tapa/tapa_form.html'
    success_url = '/tapa/'
    success_message = "Se ha creado correctamente la tapa."


class ListTapaView(ListView):
    model = Tapa
    template_name = 'tapa/tapa_list.html'
    context_object_name = 'tapas'


class UpdateTapaView(UpdateView):
    model = Tapa
    form_class = TapaForm
    template_name = 'tapa/tapa_form.html'
    success_url = '/tapa/'


class DeleteTapaView(DeleteView):
    model = Tapa
    template_name = 'tapa/tapa_confirm_delete.html'
    success_url = '/tapa/'
