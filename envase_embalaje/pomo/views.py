from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from envase_embalaje.pomo.forms import PomoForm
from envase_embalaje.pomo.models import Pomo


# Create your views here.
class CreatePomoView(CreateView):
    model = Pomo
    form_class = PomoForm
    template_name = 'pomo/pomo_form.html'
    success_url = '/pomo/'
    success_message = "Se ha creado correctamente el pomo."


class ListPomoView(ListView):
    model = Pomo
    template_name = 'pomo/pomo_list.html'
    context_object_name = 'pomos'


class UpdatePomoView(UpdateView):
    model = Pomo
    form_class = PomoForm
    template_name = 'pomo/pomo_form.html'
    success_url = '/pomo/'


class DeletePomoView(DeleteView):
    model = Pomo
    template_name = 'pomo/pomo_confirm_delete.html'
    success_url = '/pomo/'
