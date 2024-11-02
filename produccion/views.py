# views.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Produccion, EnvaseEmbalaje
from .forms import ProduccionForm

class ProduccionListView(ListView):
    model = Produccion
    template_name = 'produccion/list.html'
    context_object_name = 'produccion'

class ProduccionCreateView(CreateView):
    model = Produccion
    form_class = ProduccionForm
    template_name = 'produccion/form.html'
    success_url = reverse_lazy('produccion_list')

class ProduccionUpdateView(UpdateView):
    model = Produccion
    form_class = ProduccionForm
    template_name = 'produccion/form.html'
    success_url = reverse_lazy('produccion_list')

class ProduccionDeleteView(DeleteView):
    model = Produccion
    template_name = 'produccion/confirm_delete.html'
    success_url = reverse_lazy('produccion_list')