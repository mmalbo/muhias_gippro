from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset

from nomencladores.planta.forms import PlantaForm
from nomencladores.planta.models import Planta
from nomencladores.filters import Filtro_Planta


# Create your views here.
class CreatePlantaView(CreateView):
    model = Planta
    form_class = PlantaForm
    template_name = 'planta/form.html'
    success_url = '/planta/plantas/'
    success_message = "Se ha creado correctamente la planta."


class ListPlantaView(ListView):
    model = Planta
    template_name = 'planta/lista.html'
    context_object_name = 'plantas'

    def get_queryset(self):
        consulta = super().get_queryset()
        self.filter = Filtro_Planta(self.request.GET, queryset=consulta) #crea el objeto filtro
        if self.filter:
            prop = self.request.GET.get('propio')
            #nombre = self.request.GET.get('nombre')
            
            if prop:
                if prop=="true":
                    consulta = consulta.filter(propio = True)
                elif prop=="false":
                    consulta = consulta.filter(propio = False)
            #if nombre: 
            #    consulta = consulta.filter(nombre__icontains = nombre)
		#else:
		#	return self.filter.qs
        return consulta

    
    def get_context_data(self, **kwargs):
        # Llama al método de la clase base
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filter

        # Agrega mensajes al contexto si existen
        if 'mensaje_error' in self.request.session:
            messages.error(self.request, self.request.session.pop('mensaje_error'))
        if 'mensaje_warning' in self.request.session:
            messages.warning(self.request, self.request.session.pop('mensaje_warning'))
        if 'mensaje_succes' in self.request.session:
            messages.success(self.request, self.request.session.pop('mensaje_succes'))
        return context


class UpdatePlantaView(UpdateView):
    model = Planta
    form_class = PlantaForm
    template_name = 'planta/form.html'
    success_url = '/planta/plantas/'


class DeletePlantaView(DeleteView):
    model = Planta
    template_name = 'planta/eliminar.html'
    success_url = '/planta/plantas/'


class CreateImportView(CreateView):
    model = Planta
    form_class = PlantaForm
    template_name = 'planta/import_form.html'
    success_url = '/planta/plantas/'
    success_message = "Se ha importado correctamente los almacenes."


def importar(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')
        No_fila = 0
        plantas_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('importarPlantas')

        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                Col_Nombre = 0
                Col_Propio = 1

                for data in imported_data:
                    nombre = str(data[0]).strip() if data[0] is not None else None
                    propio_input = str(data[1]).strip().lower()  # Convertir a minúsculas
                    # Validar el campo 'propio'
                    if propio_input not in ['si', 'no']:
                        messages.error(request,
                                       f'En la fila {No_fila + 2} el valor para "Propia" debe ser "si" o "no". Valor '
                                       f'recibido: {data[2] if data[2] is not None else "Ninguno"}')
                        return redirect('importarPlantas')
                    # Validaciones
                    propio = True if propio_input == 'sí' else False
                    existe = Planta.objects.filter(nombre__iexact=nombre, propio=propio)
                    if existe:
                        plantas_existentes.append(nombre)
                        continue
                    if not nombre:
                        messages.error(request, f'En la fila {No_fila + 2} el campo "Nombre" es obligatorio.')
                        return redirect('importarPlantas')

                    propio = True if propio_input == 'sí' else False
                    try:
                        planta = Planta(
                            nombre=nombre,
                            propio=propio,

                        )
                        planta.full_clean()  # Valida los datos antes de guardar
                        planta.save()
                        No_fila += 1  # Incrementa solo si se guarda correctamente

                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        continue

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(plantas_existentes)
                    messages.success(request, f'Se han importado {Total_filas} formatos satisfactoriamente.')
                    if plantas_existentes:
                        messages.warning(request,
                                         'Las siguientes unidades de medidas ya se encontraban registradas: ' + ', '.join(
                                             plantas_existentes))
                else:
                    messages.warning(request, "No se importó ningún formato.")

                return redirect('planta_lista')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('importarPlantas')

    return render(request, 'planta/import_form.html')
