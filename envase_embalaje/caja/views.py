from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from tablib import Dataset
import re

from envase_embalaje.caja.forms import CajaForm, UpdateCajaForm
from envase_embalaje.caja.models import Caja
from envase_embalaje.filters import *



# Create your views here.
class CreateCajaView(CreateView):
    model = Caja
    form_class = CajaForm
    template_name = 'caja/caja_form.html'
    success_url = '/caja/'
    success_message = "Se ha creado correctamente la caja."


class UpdateCajaView(UpdateView):
    model = Caja
    form_class = UpdateCajaForm
    template_name = 'caja/caja_form.html'
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

    def get_queryset(self):
        consulta = super().get_queryset()
        self.filter = Filtro_Caja(self.request.GET, queryset=consulta) #crea el objeto filtro
        if self.filter:
            nombre = self.request.GET.get('nombre')
            tam = self.request.GET.get('tamanno')
            mat = self.request.GET.get('material')
            
            if nombre: 
                consulta = consulta.filter(nombre__icontains = nombre)
            if tam:
                consulta = consulta.filter(tamanno = tam)
            if mat:
                consulta = consulta.filter(material__icontains = mat)
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


def generar_formato_codigo(material, tamanno):
    """
    Genera la base del código con el formato: C + 3 letras del material + 2 letras del tamaño.
    """
    # Obtener las 3 primeras letras del material y las 2 primeras del tamaño
    material_abrev = material[:3].capitalize()
    tamanno_abrev = tamanno[:2].capitalize()

    # Construir la expresión regular para validar el formato    
    formato_esperado = re.compile(rf'C{material_abrev}{tamanno_abrev}')

    return formato_esperado.pattern

def generar_codigo(codigo_base, ultimo):
    # Verifica si hay un objeto con código base anterior
    if ultimo:
        try:
            cod_num = int(ultimo.codigo[6:9])
        except (ValueError, IndexError):
            print(f"Error: El código '{ultimo.codigo}' no tiene el formato esperado. Usando 0 como base.")

    else:
        cod_num = 1
    # se conforma un código base
    cod_num_str = str(cod_num).zfill(3)    
    codigo = f"{codigo_base}{cod_num_str}"
    # se verifica que no exista el objeto con el código conformado
    while Caja.objects.filter(codigo=codigo):
        cod_num += 1
        cod_num_str = str(cod_num).zfill(3)
        codigo = f"{codigo_base}{cod_num_str}"

    return codigo

def importarCaja(request):
    if request.method == 'POST':
        file = request.FILES.get('excelCaja')
        No_fila = 0
        cajas_existentes = []

        # Validar el archivo
        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('caja:crearImportarCaja')
        try:
            with transaction.atomic():
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                
                for data in imported_data:
                    
                    nombre = str(data[1]).strip() if data[1] is not None else None
                    tamanno = str(data[2]).strip() if data[2] is not None else None
                    material = str(data[3]).strip() if data[3] is not None else None

                    codigo_base = generar_formato_codigo(material, tamanno)
                    ultimo = Caja.objects.filter(codigo__icontains=codigo_base).first()
                    existe = Caja.objects.filter(material=material,tamanno=tamanno,nombre=nombre).first()
                    
                    if existe:
                        cajas_existentes.append(existe.nombre)
                        continue
                    else:
                        codigo = generar_codigo(codigo_base,ultimo)
                    
                    # Validaciones de los datos
                    if not nombre or not tamanno or not material:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: Los campos 'Nombre', 'Descripción' y 'Color' son "
                                       f"obligatorios.")
                        return redirect('caja:crearImportarCaja')

                    if len(nombre) > 255:
                        messages.error(request, f"Fila {No_fila + 2}: El nombre no puede exceder 255 caracteres.")
                        return redirect('caja:crearImportarCaja')

                    if len(tamanno) > 255:
                        messages.error(request, f"Fila {No_fila + 2}: El tamaño no puede exceder 255 caracteres.")
                        return redirect('caja:crearImportarCaja')

                    if len(material) > 255:
                        messages.error(request, f"Fila {No_fila + 1}: El material no puede exceder 255 caracteres.")
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
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('caja:crearImportarCaja')

                if No_fila > 0:
                    Total_filas = No_fila - len(cajas_existentes)
                    messages.success(request, f'Se han importado {Total_filas} cajas satisfactoriamente.')
                    if cajas_existentes:
                        messages.warning(request, 'Las siguientes cajas ya se encontraban registrados: ' + ', '.join(
                            cajas_existentes))
                else:
                    if cajas_existentes:
                        messages.warning(request,
                                         'No se importó ninguna caja y los siguientes códigos ya se encontraban '
                                         'registrados: ' + ', '.join(
                                             cajas_existentes))
                    else:
                        messages.warning(request, "No se importó ninguna caja.")

                return redirect('caja:listar')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('caja:listar')

    return render(request, 'caja/caja_form.html')
