from os.path import basename
from django.http import JsonResponse, Http404
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from nomencladores.almacen.models import Almacen
from materia_prima.forms import MateriaPrimaForm, MateriaPrimaFormUpdate
from materia_prima.models import MateriaPrima


class CreateMateriaPrimaView(CreateView):
    model = MateriaPrima
    form_class = MateriaPrimaForm
    template_name = 'materia_prima/materia_prima_form.html'
    success_url = reverse_lazy('materia_prima:materia_prima_list')  # Cambia esto al nombre de tu URL
    success_message = "Se ha creado correctamente la materia prima."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class ListMateriaPrimaView(ListView):
    model = MateriaPrima
    template_name = 'materia_prima/materia_prima_list.html'
    context_object_name = 'materias_primas'


class UpdateMateriaPrimaView(UpdateView):
    model = MateriaPrima
    form_class = MateriaPrimaFormUpdate
    template_name = 'materia_prima/materia_prima_form.html'
    success_url = reverse_lazy('materia_prima:materia_prima_list')  # Cambia esto al nombre de tu URL

    def form_valid(self, form):
        messages.success(self.request, "Se ha actualizado correctamente la materia prima.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.get('instance')
        if instance:
            kwargs['initial'] = {
                'tipo_materia_prima': instance.tipo_materia_prima.nombre,
                # 'factura_adquisicion': instance.get_factura_adquisicion_name,
                'ficha_tecnica': instance.get_ficha_tecnica_name,
                'hoja_seguridad': instance.get_hoja_seguridad_name,
            }
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        # context['factura_adquisicion_nombre'] = basename(obj.factura_adquisicion.name) if obj.factura_adquisicion else ''
        context['ficha_tecnica_nombre'] = basename(obj.ficha_tecnica.name) if obj.ficha_tecnica else ''
        context['hoja_seguridad_nombre'] = basename(obj.hoja_seguridad.name) if obj.hoja_seguridad else ''
        return context


class DeleteMateriaPrimaView(DeleteView):
    model = MateriaPrima
    template_name = 'materia_prima/materia_prima_confirm_delete.html'
    success_url = reverse_lazy('materia_prima_list')  # Cambia esto al nombre de tu URL


def get_materias_primas(request, pk):
    try:
        almacen = Almacen.objects.get(pk=pk)
        materias_primas = almacen.materias_primas.all()
        materias_primas_data = [{'nombre': materia_prima.nombre, 'nombre_almacen': almacen.nombre} for materia_prima in materias_primas]

        return JsonResponse(materias_primas_data, safe=False)
    except Almacen.DoesNotExist:
        raise Http404("Almacén no encontrado")