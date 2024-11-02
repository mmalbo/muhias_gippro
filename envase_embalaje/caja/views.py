from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from envase_embalaje.caja.forms import CajaForm
from envase_embalaje.caja.models import Caja


# Create your views here.
class CreateCajaView(CreateView):
    model = Caja
    form_class = CajaForm
    template_name = 'caja/caja_form.html'
    success_url = '/caja/'
    success_message = "Se ha creado correctamente la caja."


class ListCajaView(ListView):
    model = Caja
    template_name = 'caja/caja_list.html'
    context_object_name = 'cajas'


class UpdateCajaView(UpdateView):
    model = Caja
    form_class = CajaForm
    template_name = 'caja/caja_form.html'
    success_url = '/caja/'


class DeleteCajaView(DeleteView):
    model = Caja
    template_name = 'caja/caja_confirm_delete.html'
    success_url = '/caja/'
