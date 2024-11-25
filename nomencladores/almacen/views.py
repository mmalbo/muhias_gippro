import uuid

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.forms.models import ModelForm
from tablib import Dataset

from nomencladores.almacen.forms import AlmacenForm
from nomencladores.almacen.models import Almacen
from bases import forms
from django import forms

from envase_embalaje.models import EnvaseEmbalaje


# Create your views here.


class AlmacenListView(ListView):
    model = Almacen
    template_name = 'almacenes/lista.html'
    context_object_name = 'almacenes'
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


class AlmacenCreateView(CreateView):
    model = Almacen
    form_class = AlmacenForm
    template_name = 'almacenes/form.html'
    success_url = reverse_lazy('almacen_lista')
    success_message = "Se ha creado correctamente el almacén."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materias_primas'] = Almacen.objects.all()
        return context


class AlmacenUpdateView(UpdateView):
    model = Almacen
    form_class = AlmacenForm
    template_name = 'almacenes/form.html'
    success_url = reverse_lazy('almacen_lista')
    success_message = "Se ha modificado correctamente el almacén."

    def get_object(self, queryset=None):
        return self.model.objects.get(pk=str(self.kwargs['pk']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materias_primas'] = Almacen.objects.all()
        return context


class AlmacenDeleteView(DeleteView):
    model = Almacen
    template_name = 'almacenes/eliminar.html'
    success_url = '/almacen/almacenes/'


def get_almacenes(request, pk):
    try:
        envase_embalaje = EnvaseEmbalaje.objects.get(pk=pk)
        almacenes = envase_embalaje.almacen.all()
        almacen_data = [{'nombre': almacen.nombre, 'codigo': envase_embalaje.codigo_envase} for almacen in almacenes]
        return JsonResponse(almacen_data, safe=False)
    except EnvaseEmbalaje.DoesNotExist:
        raise Http404("Envase o embalaje no encontrado")


class CreateImportView(CreateView):
    model = Almacen
    form_class = AlmacenForm
    template_name = 'almacenes/import_form.html'
    success_url = '/almacen/almacenes/'


def importar(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')
        No_fila = 0
        cajas_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('importarAlmacenes')

        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                Col_Nombre = 0
                Col_Ubicacion = 1
                Col_Propio = 3

                for data in imported_data:
                    nombre = str(data[0]).strip() if data[0] is not None else None
                    ubicacion = str(data[1]).strip() if data[1] is not None else None
                    propio_input = str(data[2]).strip().lower()  # Convertir a minúsculas

                    # Validaciones
                    if not nombre or not ubicacion or nombre =='None'or ubicacion =='None':
                        messages.error(request, f'En la fila {No_fila+2} los campos "Nombre" y "Ubicación" son obligatorios.')
                        return redirect('importarAlmacenes')

                    # Validar el campo 'propio'
                    if propio_input not in ['si', 'no']:
                        messages.error(request,
                                       f'En la fila {No_fila+2} el valor para "Propio" debe ser "si" o "no". Valor '
                                       f'recibido: {data[2] if data[2] is not None else "Ninguno"}')
                        return redirect('importarAlmacenes')

                    propio = True if propio_input == 'sí' else False
                    try:
                        almacen = Almacen(
                            nombre=nombre,
                            propio=propio,
                            ubicacion=ubicacion,

                        )
                        almacen.full_clean()  # Valida los datos antes de guardar
                        almacen.save()
                        No_fila += 1  # Incrementa solo si se guarda correctamente

                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        continue

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(cajas_existentes)
                    messages.success(request, f'Se han importado {Total_filas} almcenes satisfactoriamente.')
                    if cajas_existentes:
                        messages.warning(request, 'Las siguientes unidades de medidas ya se encontraban registradas: ' + ', '.join(cajas_existentes))
                else:
                    messages.warning(request, "No se importó ningún almacén.")

                return redirect('almacen_lista')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('almacen_lista')

    return render(request, 'almacenes/import_form.html')