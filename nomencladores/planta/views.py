from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from nomencladores.planta.forms import PlantaForm
from nomencladores.planta.models import Planta


# Create your views here.
class CreatePlantaView(CreateView):
    model = Planta
    form_class = PlantaForm
    template_name = 'planta/form.html'
    success_url = '/planta/plantas/'
    success_message = "Se ha creado correctamente la planta."


class ListPlantaView(ListView):
    model = Planta
    template_name = 'planta/lista.html'
    context_object_name = 'plantas'


class UpdatePlantaView(UpdateView):
    model = Planta
    form_class = PlantaForm
    template_name = 'planta/form.html'
    success_url = '/planta/plantas/'


class DeletePlantaView(DeleteView):
    model = Planta
    template_name = 'planta/eliminar.html'
    success_url = '/planta/plantas/'
