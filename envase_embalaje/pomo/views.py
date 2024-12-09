from distutils.command.config import config

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset

from envase_embalaje.pomo.forms import PomoForm
from envase_embalaje.pomo.models import Pomo
from nomencladores.color.models import Color


# Create your views here.
class CreatePomoView(CreateView):
    model = Pomo
    form_class = PomoForm
    template_name = 'pomo/pomo_form.html'
    success_url = '/pomo/'
    success_message = "Se ha creado correctamente el pomo."


class CreateImportView(CreateView):
    model = Pomo
    form_class = PomoForm
    template_name = 'pomo/import_form.html'
    success_url = '/pomo/'


class ListPomoView(ListView):
    model = Pomo
    template_name = 'pomo/pomo_list.html'
    context_object_name = 'pomos'

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


class UpdatePomoView(UpdateView):
    model = Pomo
    form_class = PomoForm
    template_name = 'pomo/pomo_form.html'
    success_url = '/pomo/'


class DeletePomoView(DeleteView):
    model = Pomo
    template_name = 'pomo/pomo_confirm_delete.html'
    success_url = '/pomo/'


def importarPomo(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')  # Cambia el nombre de la variable si es necesario
        pomos_existentes = []
        No_fila = 0

        # Validar el archivo
        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('pomo:importarPomo')

        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)

                for index, data in enumerate(imported_data):
                    codigo = str(data[0]).strip()  # Col_Codigo
                    existe = Pomo.objects.filter(codigo__iexact=codigo).first()

                    if existe:
                        pomos_existentes.append(codigo)
                        continue

                    nombre = str(data[1]).strip() if data[1] is not None else None  # Col_Nombre
                    tamanno = str(data[3]).strip() if data[3] is not None else None  # Col_Tamanno
                    material = str(data[4]).strip() if data[4] is not None else None  # Col_Material
                    Col_Color = str(data[2]).strip() if data[2] is not None else None  # Col_Color
                    # Validaciones de los datos

                    if not nombre or not codigo or not tamanno or not material or not Col_Color:
                        messages.error(request,
                                       f"Fila {index + 2}: Los campos 'Código','Nombre', 'Forma', 'Color' y "
                                       f"'Material' son obligatorios.")
                        return redirect('pomo:importarPomo')

                    color = Color.objects.filter(nombre__iexact=Col_Color).first()
                    if color is None:
                        messages.error(request,
                                       f"Fila {index + 2}: No existe el color {Col_Color} en el nomenclador de colores")
                        return redirect('pomo:importarPomo')
                    if len(nombre) > 255:
                        messages.error(request, f"Fila {index + 2}: El nombre no puede exceder 255 caracteres.")
                        return redirect('pomo:importarPomo')

                    if len(tamanno) > 255:
                        messages.error(request, f"Fila {index + 2}: El tamaño no puede exceder 255 caracteres.")
                        return redirect('pomo:importarPomo')

                    if len(material) > 255:
                        messages.error(request, f"Fila {index + 2}: El material no puede exceder 255 caracteres.")
                        return redirect('pomo:importarPomo')

                    try:
                        pomo = Pomo(
                            codigo=codigo,
                            nombre=nombre,
                            forma=tamanno,
                            material=material,
                            color=color
                        )
                        pomo.full_clean()  # Valida los datos antes de guardar
                        pomo.save()
                        No_fila += 1
                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {index + 2}: {str(e)}")
                        return redirect('pomo:importarPomo')

                # Mensajes de resultado
                if No_fila > 0:
                    Total_filas = No_fila - len(pomos_existentes)
                    messages.success(request, f'Se han importado {Total_filas} pomos satisfactoriamente.')
                    if pomos_existentes:
                        messages.warning(request, 'Los siguientes códigos ya se encontraban registrados: ' + ', '.join(
                            pomos_existentes))
                else:
                    if pomos_existentes:
                        messages.warning(request,
                                         'No se importó ningún pomo y los siguientes códigos ya se encontraban '
                                         'registrados: ' + ', '.join(
                                             pomos_existentes))
                    else:
                        messages.warning(request, "No se importó ningún pomo.")

                return redirect('pomo:listar')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('pomo:listar')

    return render(request, 'pomo/import_form.html')
