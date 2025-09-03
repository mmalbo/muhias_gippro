import re
from os.path import basename

from django.db import transaction
from django.http import JsonResponse, Http404
from django.shortcuts import redirect, render
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from tablib import Dataset
from django.contrib.auth.decorators import login_required, user_passes_test

from nomencladores.almacen.models import Almacen
from materia_prima.forms import MateriaPrimaForm, MateriaPrimaFormUpdate
from materia_prima.models import MateriaPrima
from .forms import AgregarTipoForm
from .choices import obtener_tipos_materia_prima, eliminar_tipo_materia_prima, agregar_tipo_materia_prima

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
                #'tipo_materia_prima': instance.tipo_materia_prima.nombre,
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
        materias_primas_data = [{'nombre': materia_prima.nombre, 'nombre_almacen': almacen.nombre} for materia_prima in
                                materias_primas]

        return JsonResponse(materias_primas_data, safe=False)
    except Almacen.DoesNotExist:
        raise Http404("Materia prima no encontrado")

class CreateImportView(CreateView):
    model = MateriaPrima
    form_class = MateriaPrimaForm
    template_name = 'materia_prima/import_form.html'
    success_url = '/materia_prima/'
    success_message = "Se ha importado correctamente la materia prima."

def importar(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')
        No_fila = 0
        materia_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('materia_prima:importarMateriasPrimas')

        try:
            with (transaction.atomic()):
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                Col_Coddigo = 0
                Col_Nombre = 1
                Col_Unidad = 2
                Col_concentracion = 3
                Col_Conformacion = 4
                Col_Cantidad = 5
                Col_Costo = 6
                #Col_TipoMateria = 7
                Col_Almacen = 7
                i = 0
                while i <= len(imported_data):
                    data = imported_data[i]
                    codigo = str(data[Col_Coddigo]).strip() if data[Col_Coddigo] is not None else None

                    existe = MateriaPrima.objects.filter(codigo__iexact=codigo).first()
                    i += 1
                    if existe:
                        materia_existentes.append(codigo)
                        No_fila += 1  # Incrementa solo si se guarda correctamente
                        continue  # Si ya existe, saltamos a la siguiente fila

                    nombre = str(data[Col_Nombre]).strip() if data[
                                                                  Col_Nombre] is not None else None  # Asegúrate de que sea un string
                    unidad = str(data[Col_Unidad]).strip() if data[Col_Unidad] is not None else None
                    concentracion = str(data[Col_concentracion]).strip() if data[
                                                                                Col_concentracion] is not None else None
                    conformacion = str(data[Col_Conformacion]).strip() if data[Col_Conformacion] is not None else None
                    cantidad = str(data[Col_Cantidad]).strip() if data[Col_Cantidad] is not None else None
                    costo = str(data[Col_Costo]).strip() if data[Col_Costo] is not None else None
                    #tipo_materia_prima = str(data[Col_TipoMateria]).strip() if data[Col_TipoMateria] is not None else None
                    almacen = str(data[Col_Almacen]).strip() if data[Col_Almacen] is not None else None

                    # Validaciones de los datostipo_materia_prima,
                    if not all(
                            [codigo, nombre, concentracion,  conformacion, unidad, cantidad, costo,
                             almacen]):
                        messages.error(request, f"Fila {No_fila + 2}: Todos los campos son obligatorios.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    #tipo_materia_prima = TipoMateriaPrima.objects.filter(nombre__iexact=tipo_materia_prima).first()
                    almacen = Almacen.objects.filter(nombre__iexact=almacen).first()
                    """ if tipo_materia_prima is None:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: No existe el tipo de materia prima  '{str(data[Col_TipoMateria]).strip()}' en el nomenclador")
                        return redirect('materia_prima:importarMateriasPrimas') """
                    if almacen is None:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: No existe el almacén  '{str(data[Col_Almacen]).strip()}' en el nomenclador")
                        return redirect('materia_prima:importarMateriasPrimas')
                    if len(nombre) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: El nombre de la materia prima no puede exceder 255 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')
                    if len(codigo) > 20:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: El código no puede exceder 20 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')
                    if len(unidad) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: La unidad de medida no puede exceder 255 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    if len(conformacion) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: La conformación no puede exceder 255 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    # Validación de capacidad
                    if not concentracion.isdigit() or int(concentracion) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: 'Concentración' debe ser un número entero mayor que cero.")
                        return redirect('materia_prima:importarMateriasPrimas')
                    # Validación de capacidad
                    if not cantidad.isdigit() or int(cantidad) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: 'Cantidad' debe ser un número entero mayor que cero.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    if not re.match(r'^-?\d+(\.\d+)?$', costo) or float(costo) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 2}: 'Costo' debe ser un número decimal válido mayor que cero.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    costo = float(costo)  # Convertimos a entero después de la validación
                    concentracion = int(concentracion)  # Convertimos a entero después de la validación
                    cantidad = int(cantidad)  # Convertimos a entero después de la validación

                    try:
                        materia_prima = MateriaPrima(
                            codigo=codigo,
                            nombre=nombre,
                            # estado=estado,
                            #tipo_materia_prima=tipo_materia_prima,  # Asumiendo que este es el ID
                            conformacion=conformacion,
                            unidad_medida=unidad,
                            concentracion=concentracion,
                            cantidad_almacen=cantidad,
                            costo=costo,
                            almacen=almacen,  # Asumiendo que este es el ID
                        )
                        materia_prima.clean()  # Valida los datos antes de guardar
                        materia_prima.save()
                        No_fila += 1  # Incrementa solo si se guarda correctamente

                    except Exception as e:
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('materia_prima:importarMateriasPrimas')

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(materia_existentes)
                    messages.success(request, f'Se han importado {Total_filas} materias primas satisfactoriamente.')
                    if materia_existentes:
                        messages.warning(request,
                                         'Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             materia_existentes))
                        return redirect('materia_prima:importarMateriasPrimas')

                else:
                    if materia_existentes:
                        messages.warning(request,
                                         'Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             materia_existentes))
                        return redirect('materia_prima:importarMateriasPrimas')
                    else:
                        messages.warning(request, "No se importó ningún formato.")
                        return redirect('materia_prima:importarMateriasPrimas')

                return redirect('materia_prima:materia_prima_list')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('materia_prima:materia_prima_list')
    return render(request, 'materia_prima/import_form.html')

###Gestionar Tipos de MP

#@login_required
def gestionar_tipos_MP(request):
    # Obtener todas las categorías
    print("entre en view gestionar")
    tipos_mp = obtener_tipos_materia_prima()
    
    # Separar categorías base y dinámicas
    from .choices import Tipo_mat_prima
    categorias_base = Tipo_mat_prima
    categorias_dinamicas = [cat for cat in tipos_mp if cat not in Tipo_mat_prima]
           
    if request.method == 'POST':
        form = AgregarTipoForm(request.POST)
        if form.is_valid():
            valor = form.cleaned_data['valor']
            etiqueta = form.cleaned_data['etiqueta']
            
            if agregar_tipo_materia_prima(valor, etiqueta):
                messages.success(request, f'Tipo de materia prima "{etiqueta}" agregada exitosamente!')
                return redirect('materia_prima:gestionar_tipos_categorias')
            else:
                messages.error(request, 'Error al agregar el tipo de materia prima')
    else:
        form = AgregarTipoForm()
    
    context = {
        'form': form,
        'categorias_base': categorias_base,
        'categorias_dinamicas': categorias_dinamicas,
        'total_categorias': len(tipos_mp),
    }
    print("ya casi")
    return render(request, 'materia_prima/gestionar_tipos.html', context)

#@login_required
def eliminar_tipos_MP(request, valor):
    if request.method == 'POST':
        # Verificar si hay materias primas usando esta categoría
        conteo = MateriaPrima.objects.filter(tipo_materia_prima=valor).count()
        
        if conteo > 0:
            messages.error(
                request, 
                f'No se puede eliminar el tipo de materia prima. Hay {conteo} materias primas usando esta categoría.'
            )
        else:
            if eliminar_tipo_materia_prima(valor):
                messages.success(request, 'Categoría eliminada exitosamente!')
            else:
                messages.error(request, 'Error al eliminar la categoría')
    
    return redirect('materia_prima:gestionar_tipos_categorias')