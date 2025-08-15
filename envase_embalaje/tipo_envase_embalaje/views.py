from django.views.generic import ListView
from envase_embalaje.caja.models import Caja
from envase_embalaje.pomo.models import Pomo
from envase_embalaje.tanque.models import Tanque
from envase_embalaje.tapa.models import Tapa


class TipoEnvaseEmbalajeListView(ListView):
    template_name = 'tipo_envase_embalaje/list.html'
    context_object_name = 'tipos_envase_embalaje'

    def get_queryset(self):
        # Obtener todos los objetos de las clases hijas
        cajas = Caja.objects.all()
        pomos = Pomo.objects.all()
        tanques = Tanque.objects.all()
        tapas = Tapa.objects.all()

        # Combinar todos los objetos en una sola lista
        tipos_envase_embalaje = list(cajas) + list(pomos) + list(tanques)+list(tapas)

        return tipos_envase_embalaje

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar el tipo a cada objeto en el contexto
        for item in context[self.context_object_name]:
            item.tipo = item.__class__.__name__  # Agregar el tipo dinámicamente
        return context