from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from envase_embalaje.forms import EnvaseEmbalajeForm, EnvaseEmbalajeUpdateForm
from envase_embalaje.models import EnvaseEmbalaje
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from nomencladores.almacen.models import Almacen
from inventario.models import Inv_Envase
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse, Http404

# Create your views here.

class ListEnvaseEmbalajeView(ListView):
    model = EnvaseEmbalaje
    template_name = 'envase_embalaje/envase_cat.html'
    context_object_name = 'envase_embalaje'
    #Hacer un query para mostrar solo los envases de un almacen si el usuario es almacenero, el almacen al que el pertenece

    def get_context_data(self, **kwargs):
        # Llama al método de la clase base
        context = super().get_context_data(**kwargs)

        # Agrega mensajes al contexto si existen
        if 'mensaje_error' in self.request.session:
            messages.error(self.request, self.request.session.pop('mensaje_error'))
        if 'mensaje_warning' in self.request.session:
            messages.warning(self.request, self.request.session.pop('mensaje_warning'))
        if 'mensaje_succes' in self.request.session:
            messages.success(self.request, self.request.session.pop('mensaje_succes'))
        return context

@login_required
def listEnvaseEmbalaje(request):
    almacen_id = request.GET.get('almacen')
    producto_id = request.GET.get('producto')
    
    almacen = None
    if request.user.groups.filter(name='Almaceneros').exists():
        almacen = Almacen.objects.filter(responsable=request.user).first()

    envase_embalaje = Inv_Envase.objects.select_related('envase', 'almacen')
    
    if request.user.groups.filter(name='Presidencia-Admin').exists() or request.user.is_staff:
        if almacen_id and almacen_id != 'todos':
            envase_embalaje = envase_embalaje.filter(almacen=almacen_id)
    else:
        if almacen:
            envase_embalaje = envase_embalaje.filter(almacen=almacen)
        else:
            envase_embalaje = Inv_Envase.objects.none()

    if producto_id:
        envase_embalaje = envase_embalaje.filter(envase=producto_id)

    envase_embalaje = envase_embalaje.order_by('envase__codigo_envase', 'almacen__nombre')
    almacenes = Almacen.objects.all()
    productos = EnvaseEmbalaje.objects.all()
    total_productos = envase_embalaje.count()

    print(envase_embalaje)

    context = {
        'envase_embalaje':envase_embalaje,
        'almacenes':almacenes,
        'productos':productos,
        'almacen_id':almacen_id,
        'producto_id':producto_id,
        'almacen':almacen,
        'total_productos':total_productos,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'envase_embalaje/envase_list.html', context)

class UpdateEnvaseEmbalajeView(UpdateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeUpdateForm
    template_name = 'envase_embalaje/envase_embalaje_form.html'
    success_url = reverse_lazy('envase_embalaje_lista')  # Cambia esto al nombre de tu URL

    def form_valid(self, form):
        messages.success(self.request, "Se ha actualizado correctamente el envase o embalaje.")
        return super().form_valid(form)

    """ def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.get('instance')
        if instance:
            kwargs['initial'] = {
                'ficha_tecnica': instance.get_ficha_tecnica_name,
                'hoja_seguridad': instance.get_hoja_seguridad_name,
            }
        return kwargs """

    """ def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        # context['factura_adquisicion_nombre'] = basename(obj.factura_adquisicion.name) if obj.factura_adquisicion else ''
        context['ficha_tecnica_nombre'] = basename(obj.ficha_tecnica.name) if obj.ficha_tecnica else ''
        context['hoja_seguridad_nombre'] = basename(obj.hoja_seguridad.name) if obj.hoja_seguridad else ''
        return context """

class DeleteEnvaseEmbalajeView(DeleteView):
    model = EnvaseEmbalaje
    template_name = 'envase_embalaje/envase_embalaje_confirm_delete.html'
    success_url = reverse_lazy('envase_embalaje_list')  # Cambia esto al nombre de tu URL

def get_envase_embalaje(request, pk):
    try:
        almacen = Almacen.objects.get(pk=pk)
        envases_embalajes = almacen.envase_embalaje.all()
        envase_embalaje_data = [{'nombre': envase_embalaje.codigo_envase, 'nombre_almacen': almacen.nombre} for envase_embalaje in
                                envases_embalajes]

        return JsonResponse(envase_embalaje_data, safe=False)
    except Almacen.DoesNotExist:
        raise Http404("Envase o embalaje no encontrado")

class CreateImportView(CreateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeForm
    template_name = 'envase_embalaje/import_form.html'
    success_url = '/envase_embalaje/'
    success_message = "Se ha importado correctamente el envase o embalaje."

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
"""
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
    success_url = reverse_lazy('envase_embalaje_lista') """
