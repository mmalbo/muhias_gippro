from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset
from envase_embalaje.caja.forms import CajaForm
from envase_embalaje.caja.models import Caja


# Create your views here.
class CreateCajaView(CreateView):
    model = Caja
    form_class = CajaForm
    template_name = 'caja/caja_form.html'
    success_url = '/caja/'
    success_message = "Se ha creado correctamente la caja."


class UpdateCajaView(UpdateView):
    model = Caja
    form_class = CajaForm
    template_name = 'caja/import_caja_form.html'
    success_url = '/caja/'


class DeleteCajaView(DeleteView):
    model = Caja
    template_name = 'caja/caja_confirm_delete.html'
    success_url = '/caja/'


class CreateImportCajaView(CreateView):
    model = Caja
    form_class = CajaForm
    template_name = 'caja/import_caja_form.html'
    success_url = '/caja/'
    success_message = "Se ha importd correctamente la caja."


class ListCajaView(ListView):
    model = Caja
    template_name = 'caja/caja_list.html'
    context_object_name = 'cajas'

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


def importarCaja(request):
    if request.method == 'POST':
        file = request.FILES.get('excelCaja')
        No_fila = 0
        cajas_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('caja:crearImportarCaja')
        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                Col_Codigo = 0
                Col_Nombre = 1
                Col_Tamanno = 2
                Col_Material = 3

                for data in imported_data:
                    codigo = str(data[Col_Codigo])
                    existe = Caja.objects.filter(codigo=codigo).first()

                    if existe:
                        cajas_existentes.append(codigo)
                        continue
                    nombre = str(data[Col_Nombre]).strip() if data[Col_Nombre] is not None else None
                    tamanno = str(data[Col_Tamanno]).strip()if data[Col_Tamanno] is not None else None
                    material = str(data[Col_Material]).strip()if data[Col_Material] is not None else None

                    # Validaciones de los datos
                    if not nombre or not tamanno or not material:
                        messages.error(request,
                                       f"Fila {No_fila +2 }: Los campos 'Nombre', 'Tamaño' y 'Material' son obligatorios.")
                        return redirect('caja:crearImportarCaja')

                    if len(nombre) > 255:
                        messages.error(request, f"Fila {No_fila +2}: El nombre no puede exceder 255 caracteres.")
                        return redirect('caja:crearImportarCaja')

                    if len(tamanno) > 255:
                        messages.error(request, f"Fila {No_fila +2}: El tamaño no puede exceder 255 caracteres.")
                        return redirect('caja:crearImportarCaja')

                    if len(material) > 255:
                        messages.error(request, f"Fila {No_fila +1 }: El material no puede exceder 255 caracteres.")
                        return redirect('caja:crearImportarCaja')

                    try:

                        caja = Caja(
                            codigo=codigo,
                            nombre=nombre,
                            tamanno=tamanno,
                            material=material
                        )
                        caja.full_clean()  # Valida los datos antes de guardar
                        caja.save()
                        No_fila += 1
                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila +2}: {str(e)}")
                        return redirect('caja:crearImportarCaja')

                if No_fila > 0:
                    Total_filas = No_fila - len(cajas_existentes)
                    messages.success(request, f'Se han importado {Total_filas} cajas satisfactoriamente.')
                    if cajas_existentes:
                        messages.warning(request, 'Los siguientes códigos ya se encontraban registrados: ' + ', '.join(
                            cajas_existentes))
                else:
                    messages.warning(request, "No se importó ninguna caja.")

                return redirect('caja:listar')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('caja:listar')

    return render(request, 'caja/caja_form.html')