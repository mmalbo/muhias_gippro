from django.db.models.functions import Concat
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.db.models import Value, CharField


class CustomUserListView(ListView):
    model = User
    template_name = 'usuario/list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        return User.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
        ).order_by('full_name')

    # def get_queryset(self):
    #     return User.objects.filter(is_active=True)


class CustomUserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('customuser_list')
    template_name = 'usuario/create.html'


class CustomUserUpdateView(UpdateView):
    model = User
    form_class = CustomUserChangeForm
    success_url = reverse_lazy('customuser_list')
    template_name = 'usuario/create.html'


class CustomUserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy('customuser_list')
    template_name = 'usuario/delete.html'

    def form_valid(self, form):
        obj = self.get_object()
        obj.is_active = False
        obj.save()
        return HttpResponseRedirect(self.get_success_url())
