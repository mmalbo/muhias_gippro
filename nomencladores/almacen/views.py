import uuid

from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.forms.models import ModelForm

from nomencladores.almacen.forms import AlmacenForm
from nomencladores.almacen.models import Almacen
from bases import forms
from django import forms

from envase_embalaje.models import EnvaseEmbalaje


# Create your views here.


class AlmacenListView(ListView):
    model = Almacen
    template_name = 'almacenes/lista.html'
    context_object_name = 'almacenes'


class AlmacenCreateView(CreateView):
    model = Almacen
    form_class = AlmacenForm
    template_name = 'almacenes/form.html'
    success_url = reverse_lazy('almacen_lista')
    success_message = "Se ha creado correctamente el almacén."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materias_primas'] = Almacen.objects.all()
        return context


class AlmacenUpdateView(UpdateView):
    model = Almacen
    form_class = AlmacenForm
    template_name = 'almacenes/form.html'
    success_url = reverse_lazy('almacen_lista')
    success_message = "Se ha modificado correctamente el almacén."

    def get_object(self, queryset=None):
        return self.model.objects.get(pk=str(self.kwargs['pk']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materias_primas'] = Almacen.objects.all()
        return context


class AlmacenDeleteView(DeleteView):
    model = Almacen
    template_name = 'almacenes/eliminar.html'
    success_url = '/almacen/almacenes/'


def get_almacenes(request, pk):
    try:
        envase_embalaje = EnvaseEmbalaje.objects.get(pk=pk)
        almacenes = envase_embalaje.almacen.all()
        almacen_data = [{'nombre': almacen.nombre, 'codigo': envase_embalaje.codigo_envase} for almacen in almacenes]
        return JsonResponse(almacen_data, safe=False)
    except EnvaseEmbalaje.DoesNotExist:
        raise Http404("Envase o embalaje no encontrado")
