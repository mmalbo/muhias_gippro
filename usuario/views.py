from django.db.models.functions import Concat
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.models import User, Group
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.db.models import Value, CharField

from .models import CustomUser


class CustomUserListView(ListView):
    model = CustomUser
    template_name = 'usuario/list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        return CustomUser.objects.filter(is_active=True).annotate(
            full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
        ).order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all()  # Puedes agregar grupos si deseas mostrar información sobre ellos
        return context


class CustomUserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('customuser_list')
    template_name = 'usuario/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all()  # Pasar grupos para selección
        return context

    def form_valid(self, form):
        username = form.cleaned_data['username']
        group = form.cleaned_data['groups'] 
        group_objects = Group.objects.filter(name=group)
        try:
            user = CustomUser.objects.get(username=username)
            if not user.is_active:
                user.is_active = True  # Activar el usuario
                user.save()

                # Limpiar y actualizar grupo
                user.groups.clear()
                # Agregar el grupo seleccionado al usuario
                user.groups.add(
                    group_objects)  # Asignar los roles seleccionados al campo 'groups'

                return super().form_valid(form)
            else:
                form.add_error('username', 'Ya existe un usuario con ese nombre.')
                return self.form_invalid(form)
        except CustomUser.DoesNotExist:
            # Si el usuario no existe, crearlo
            user = form.save(commit=False)
            user.save()

            # Asignar grupo
            # Agregar el grupo seleccionado al usuario
            user.groups.add(
                group_objects)  # Asignar los roles seleccionados al campo 'groups'
        return super().form_valid(form)


class CustomUserUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    success_url = reverse_lazy('customuser_list')
    template_name = 'usuario/update.html'  # Cambia a 'update.html' para reflejar la acción

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all()  # Pasar grupos para selección
        return context

    def form_valid(self, form):
        # Guarda el usuario
        user = form.save(commit=False)
        user.save()

        # Asignar grupos si se selecciona alguno
        groups = self.request.POST.getlist('groups')  # Suponiendo que hay un campo 'groups' en el formulario
        user.groups.clear()  # Limpia los grupos anteriores
        for group_id in groups:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)

        return super().form_valid(form)


class CustomUserDeleteView(DeleteView):
    model = CustomUser
    success_url = reverse_lazy('customuser_list')
    template_name = 'usuario/delete.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False  # Desactiva el usuario
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())
