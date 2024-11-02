from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from envase_embalaje.tanque.forms import TanqueForm
from envase_embalaje.tanque.models import Tanque


# Create your views here.
class CreateTanqueView(CreateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'tanque/tanque_form.html'
    success_url = '/tanque/'
    success_message = "Se ha creado correctamente el tanque."


class ListTanqueView(ListView):
    model = Tanque
    template_name = 'tanque/tanque_list.html'
    context_object_name = 'tanques'


class UpdateTanqueView(UpdateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'tanque/tanque_form.html'
    success_url = '/tanque/'


class DeleteTanqueView(DeleteView):
    model = Tanque
    template_name = 'tanque/tanque_confirm_delete.html'
    success_url = '/tanque/'
