from csv import unix_dialect

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset

from envase_embalaje.formato.forms import FormatoForm
from envase_embalaje.formato.models import Formato


# Create your views here.
class CreateFormatoView(CreateView):
    model = Formato
    form_class = FormatoForm
    template_name = 'capacidad/capacidad_form.html'
    success_url = '/formato/lista/'
    success_message = "Se ha creado correctamente la capacidad."


class ListFormatoView(ListView):
    model = Formato
    template_name = 'capacidad/capacidad_list.html'
    context_object_name = 'capacidades'

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


class UpdateFormatoView(UpdateView):
    model = Formato
    form_class = FormatoForm
    template_name = 'capacidad/capacidad_form.html'
    success_url = '/formato/lista/'


class DeleteCapacidadView(DeleteView):
    model = Formato
    template_name = 'capacidad/capacidad_confirm_delete.html'
    success_url = '/formato/lista/'


class CreateImportView(CreateView):
    model = Formato
    form_class = FormatoForm
    template_name = 'capacidad/import_form.html'
    success_url = '/formato/lista/'
    success_message = "Se ha importado correctamente el formato."


def importar(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')
        No_fila = 0
        formatos_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('formato:importarFormato')

        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                Col_Unidad = 0
                Col_Capacidad = 1

                for data in imported_data:
                    unidad = str(data[Col_Unidad]).strip() if data[Col_Unidad] is not None else None
                    capacidad = str(data[Col_Capacidad]).strip()  # Asegúrate de que sea un string
                    existe = Formato.objects.filter(unidad_medida__iexact=unidad, capacidad=capacidad).first() if data[
                                                                                                              Col_Capacidad] is not None else None

                    if existe:
                        formatos_existentes.append(unidad)
                        continue  # Si ya existe, saltamos a la siguiente fila



                    # Validaciones de los datos
                    if not unidad or not capacidad:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: Los campos 'Unidad de medida' y 'Capacidad' son obligatorios.")
                        return redirect('formato:importarFormato')

                    if len(unidad) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: La unidad de medida no puede exceder 255 caracteres.")
                        return redirect('formato:importarFormato')

                    # Validación de capacidad
                    if not capacidad.isdigit() or int(capacidad) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: 'Capacidad' debe ser un número entero mayor que cero.")
                        return redirect('formato:importarFormato')

                    capacidad = int(capacidad)  # Convertimos a entero después de la validación

                    try:
                        formato = Formato(
                            unidad_medida=unidad,
                            capacidad=capacidad,
                        )
                        formato.full_clean()  # Valida los datos antes de guardar
                        formato.save()
                        No_fila += 1  # Incrementa solo si se guarda correctamente

                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('formato:importarFormato')

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(formatos_existentes)
                    messages.success(request, f'Se han importado {Total_filas} formatos satisfactoriamente.')
                    if formatos_existentes:
                        messages.warning(request,
                                         'Los siguientes formatos ya se encontraban registrados: ' + ', '.join(
                                             formatos_existentes))
                else:
                    if formatos_existentes:
                        messages.warning(request,
                                         'No se importó ningún formato y los siguientes formatos ya se encontraban '
                                         'registrados: ' + ', '.join(
                                             formatos_existentes))
                    else:
                        messages.warning(request, "No se importó ningún formato.")

                return redirect('formato:listar')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('formato:listar')

    return render(request, 'capacidad/import_form.html')
