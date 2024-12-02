from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset

from envase_embalaje.tanque.forms import TanqueForm
from envase_embalaje.tanque.models import Tanque
from nomencladores.color.models import Color


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



class UpdateTanqueView(UpdateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'tanque/tanque_form.html'
    success_url = '/tanque/'


class DeleteTanqueView(DeleteView):
    model = Tanque
    template_name = 'tanque/tanque_confirm_delete.html'
    success_url = '/tanque/'


class CreateImportView(CreateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'tanque/import_form.html'
    success_url = '/tanque/'


def importarTanque(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')  # Cambia el nombre de la variable si es necesario
        tanques_existentes = []
        No_fila = 0

        # Validar el archivo
        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('tanque:importarTanque')

        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)

                for index, data in enumerate(imported_data):
                    codigo = str(data[0]).strip()  # Col_Codigo
                    existe = Tanque.objects.filter(codigo__iexact=codigo).first()

                    if existe:
                        tanques_existentes.append(codigo)
                        continue

                    nombre = str(data[1]).strip() if data[1] is not None else None  # Col_Nombre
                    material = str(data[3]).strip() if data[3] is not None else None  # Col_Material
                    Col_Color = str(data[2]).strip() if data[2] is not None else None  # Col_Color
                    # Validaciones de los datos

                    if not nombre or not codigo or not material or not Col_Color:
                        messages.error(request,
                                       f"Fila {index + 2}: Los campos 'Código','Nombre', 'Color' y 'Material' son "
                                       f"obligatorios.")
                        return redirect('tanque:importarTanque')

                    color = Color.objects.filter(nombre__iexact=Col_Color).first()
                    if color is None:
                        messages.error(request,
                                       f"Fila {index + 2}: No existe el color {Col_Color} en el nomenclador de colores")
                        return redirect('tanque:importarTanque')
                    if len(nombre) > 255:
                        messages.error(request, f"Fila {index + 2}: El nombre no puede exceder 255 caracteres.")
                        return redirect('tanque:importarTanque')

                    if len(material) > 255:
                        messages.error(request, f"Fila {index + 2}: El material no puede exceder 255 caracteres.")
                        return redirect('tanque:importarTanque')

                    try:
                        tanque = Tanque(
                            codigo=codigo,
                            nombre=nombre,
                            material=material,
                            color=color
                        )
                        tanque.full_clean()  # Valida los datos antes de guardar
                        tanque.save()
                        No_fila += 1
                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {index + 2}: {str(e)}")
                        return redirect('tanque:importarTanque')

                # Mensajes de resultado
                if No_fila > 0:
                    Total_filas = No_fila - len(tanques_existentes)
                    messages.success(request, f'Se han importado {Total_filas} tanques satisfactoriamente.')
                    if tanques_existentes:
                        messages.warning(request, 'Los siguientes códigos ya se encontraban registrados: ' + ', '.join(
                            tanques_existentes))
                else:
                    if tanques_existentes:
                        messages.warning(request,
                                         'No se importó ningún tanque y los siguientes códigos ya se encontraban '
                                         'registrados: ' + ', '.join(
                                             tanques_existentes))
                    else:
                        messages.warning(request, "No se importó ningún tanque.")

                return redirect('tanque:listar')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('tanque:listar')

    return render(request, 'tanque/import_form.html')
