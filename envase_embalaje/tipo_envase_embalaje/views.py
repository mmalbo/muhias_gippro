from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from tipo_envase_embalaje.forms import TipoEnvaseEmbalajeForm
from tipo_envase_embalaje.models import TipoEnvaseEmbalaje


class TipoEnvaseEmbalajeListView(ListView):
    model = TipoEnvaseEmbalaje
    template_name = 'tipo_envase_embalaje/list.html'
    context_object_name = 'tipos_envase_embalaje'


class TipoEnvaseEmbalajeCreateView(CreateView):
    model = TipoEnvaseEmbalaje
    form_class = TipoEnvaseEmbalajeForm
    success_url = reverse_lazy('tipo_envase_embalaje_list')
    template_name = 'tipo_envase_embalaje/create.html'


class TipoEnvaseEmbalajeUpdateView(UpdateView):
    model = TipoEnvaseEmbalaje
    form_class = TipoEnvaseEmbalajeForm
    success_url = reverse_lazy('tipo_envase_embalaje_list')
    template_name = 'tipo_envase_embalaje/update.html'


class TipoEnvaseEmbalajeDeleteView(DeleteView):
    model = TipoEnvaseEmbalaje
    success_url = reverse_lazy('tipo_envase_embalaje_list')
    template_name = 'tipo_envase_embalaje/delete.html'


context_object_name = 'lista_tipo_envase_embalaje'
