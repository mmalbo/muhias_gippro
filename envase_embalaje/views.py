from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from envase_embalaje.forms import EnvaseEmbalajeForm, EnvaseEmbalajeUpdateForm
from envase_embalaje.models import EnvaseEmbalaje


# Create your views here.


class EnvaseEmbalajeListView(ListView):
    model = EnvaseEmbalaje
    template_name = 'envase_embalaje/lista.html'
    context_object_name = 'envases_embalajes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar el tipo a cada objeto en el contexto
        for item in context[self.context_object_name]:
            item.tipo = item.__class__.__name__  # Agregar el tipo dinámicamente
        return context

class EnvaseEmbalajeCreateView(CreateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeForm
    template_name = 'envase_embalaje/form.html'
    success_url = reverse_lazy('envase_embalaje_lista')
    success_message = "Se ha creado correctamente el almacén."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['almacenes'] = EnvaseEmbalaje.objects.all()
        return context

class EnvaseEmbalajeUpdateView(UpdateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeUpdateForm
    template_name = 'envase_embalaje/form.html'
    success_url = reverse_lazy('envase_embalaje_lista')
    success_message = "Se ha modificado correctamente el almacén."

    def get_object(self, queryset=None):
        return self.model.objects.get(pk=str(self.kwargs['pk']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['almacenes'] = EnvaseEmbalaje.objects.all()
        return context

class EnvaseEmbalajeDeleteView(DeleteView):
    model = EnvaseEmbalaje
    template_name = 'envase_embalaje/eliminar.html'
    success_url = reverse_lazy('envase_embalaje_lista')
