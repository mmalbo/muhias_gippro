from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset

from envase_embalaje.tapa.forms import TapaForm
from envase_embalaje.tapa.models import Tapa
from nomencladores.color.models import Color


# Create your views here.
class CreateTapaView(CreateView):
    model = Tapa
    form_class = TapaForm
    template_name = 'tapa/tapa_form.html'
    success_url = '/tapa/'
    success_message = "Se ha creado correctamente la tapa."


class ListTapaView(ListView):
    model = Tapa
    template_name = 'tapa/tapa_list.html'
    context_object_name = 'tapas'

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


class UpdateTapaView(UpdateView):
    model = Tapa
    form_class = TapaForm
    template_name = 'tapa/tapa_form.html'
    success_url = '/tapa/'


class DeleteTapaView(DeleteView):
    model = Tapa
    template_name = 'tapa/tapa_confirm_delete.html'
    success_url = '/tapa/'


class CreateImportView(CreateView):
    model = Tapa
    form_class = TapaForm
    template_name = 'tapa/import_form.html'
    success_url = '/tapa/'


def importarTapa(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')  # Cambia el nombre de la variable si es necesario
        tapa_existentes = []
        No_fila = 0

        # Validar el archivo
        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('tapa:importarTapa')

        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)

                for index, data in enumerate(imported_data):
                    codigo = str(data[0]).strip()  # Col_Codigo
                    existe = Tapa.objects.filter(codigo__iexact=codigo).first()

                    if existe:
                        tapa_existentes.append(codigo)
                        continue

                    nombre = str(data[1]).strip() if data[1] is not None else None  # Col_Nombre
                    descripcion = str(data[3]).strip() if data[3] is not None else None  # Col_descripcion
                    Col_Color = str(data[2]).strip() if data[2] is not None else None  # Col_Color
                    # Validaciones de los datos

                    if not nombre or not codigo or not descripcion or not Col_Color:
                        messages.error(request,
                                       f"Fila {index + 2}: Los campos 'Código','Nombre', 'Descripción' y 'Color' son "
                                       f"obligatorios.")
                        return redirect('tapa:importarTapa')

                    color = Color.objects.filter(nombre__iexact=Col_Color).first()
                    if color is None:
                        messages.error(request,
                                       f"Fila {index + 2}: No existe el color {Col_Color} en el nomenclador de colores")
                        return redirect('tapa:importarTapa')
                    if len(nombre) > 255:
                        messages.error(request, f"Fila {index + 2}: El nombre no puede exceder 255 caracteres.")
                        return redirect('tapa:importarTapa')

                    if len(descripcion) > 255:
                        messages.error(request, f"Fila {index + 2}: El tamaño no puede exceder 255 caracteres.")
                        return redirect('tapa:importarTapa')

                    try:
                        tapa = Tapa(
                            codigo=codigo,
                            nombre=nombre,
                            descripcion=descripcion,
                            color=color
                        )
                        tapa.full_clean()  # Valida los datos antes de guardar
                        tapa.save()
                        No_fila += 1
                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {index + 2}: {str(e)}")
                        return redirect('tapa:importarTapa')

                # Mensajes de resultado
                if No_fila > 0:
                    Total_filas = No_fila - len(tapa_existentes)
                    messages.success(request, f'Se han importado {Total_filas} tapas satisfactoriamente.')
                    if tapa_existentes:
                        messages.warning(request, 'Los siguientes códigos ya se encontraban registrados: ' + ', '.join(
                            tapa_existentes))
                else:
                    if tapa_existentes:
                        messages.warning(request,
                                         'No se importó ninguna tapa y los siguientes códigos ya se encontraban '
                                         'registrados: ' + ', '.join(
                                             tapa_existentes))
                    else:
                        messages.warning(request, "No se importó ninguna tapa.")

                return redirect('tapa:listar')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('tapa:listar')

    return render(request, 'tapa/import_form.html')
