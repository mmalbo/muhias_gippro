import re

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset

from envase_embalaje.tanque.forms import TanqueForm, UpdateTanqueForm
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
    form_class = UpdateTanqueForm
    template_name = 'tanque/tanque_form.html'
    success_url = reverse_lazy('tanque:listar')  # Usar reverse_lazy para la URL de éxito


class DeleteTanqueView(DeleteView):
    model = Tanque
    template_name = 'tanque/tanque_confirm_delete.html'
    success_url = '/tanque/'


class CreateImportView(CreateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'tanque/import_form.html'
    success_url = '/tanque/'


def generar_formato_codigo(material, color):
    """
    Valida que el código tenga el formato: P + 3 letras del material + 3 letras del color + 3 dígitos consecutivos.
    """
    # Obtener las 3 primeras letras del material y las 2 primeras del tamaño
    material_abrev = material[:3].capitalize()
    color_abrev = color[:3].capitalize()

    # Construir la expresión regular para validar el formato
    formato_esperado = re.compile(rf'T{material_abrev}{color_abrev}')

    return formato_esperado.pattern

def generar_codigo(codigo_base, ultimo):
    # Verifica si hay un objeto con código base anterior
    if ultimo:
        try:
            cod_num = int(ultimo.codigo[7:10])
        except (ValueError, IndexError):
            print(f"Error: El código '{ultimo.codigo}' no tiene el formato esperado. Usando 0 como base.")

    else:
        cod_num = 1
    # se conforma un código base
    cod_num_str = str(cod_num).zfill(3)    
    codigo = f"{codigo_base}{cod_num_str}"
    # se verifica que no exista el objeto con el código conformado
    while Tanque.objects.filter(codigo=codigo):
        cod_num += 1
        cod_num_str = str(cod_num).zfill(3)
        codigo = f"{codigo_base}{cod_num_str}"

    return codigo

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

                for data in imported_data:

                    nombre = str(data[1]).strip() if data[1] is not None else None  # Col_Nombre
                    material = str(data[3]).strip() if data[3] is not None else None  # Col_Material
                    Col_Color = str(data[2]).strip() if data[2] is not None else None  # Col_Color
                    print(Col_Color)
                    color = Color.objects.filter(nombre=Col_Color).first()
                    print("---Var color---")
                    print(color.id)
                    print(color.nombre)
                    codigo_base = generar_formato_codigo(material,color.nombre)  # Col_Codigo
                    ultimo = Tanque.objects.filter(codigo__icontains=codigo_base).first()
                    existe = Tanque.objects.filter(nombre=nombre, material=material,color=color.id).first()

                    if existe:
                        tanques_existentes.append(existe.nombre)
                        continue
                    else:
                        codigo = generar_codigo(codigo_base, ultimo)                    

                    # Validaciones de los datos

                    if not nombre or not material or not Col_Color:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: Los campos 'Nombre', 'Color' y 'Material' son "
                                       f"obligatorios.")
                        return redirect('tanque:importarTanque')

                    if color is None:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: No existe el color {Col_Color} en el nomenclador de colores")
                        return redirect('tanque:importarTanque')

                    if len(nombre) > 255:
                        messages.error(request, f"Fila {No_fila + 2}: El nombre no puede exceder 255 caracteres.")
                        return redirect('tanque:importarTanque')

                    if len(material) > 255:
                        messages.error(request, f"Fila {No_fila + 2}: El material no puede exceder 255 caracteres.")
                        return redirect('tanque:importarTanque')

                    try:
                        print("---color en try---")
                        print(color)
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
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
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
