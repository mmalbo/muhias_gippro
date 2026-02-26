import re
from os.path import basename

from django.db import transaction
from django.http import JsonResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from tablib import Dataset
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date, datetime, timezone
from nomencladores.almacen.models import Almacen
from materia_prima.forms import MateriaPrimaForm, MateriaPrimaFormUpdate, MateriaPrimaCostoForm
from materia_prima.models import MateriaPrima
from inventario.models import Inv_Mat_Prima
from .forms import AgregarTipoForm
from .choices import obtener_tipos_materia_prima, eliminar_tipo_materia_prima, agregar_tipo_materia_prima
import decimal

class CreateMateriaPrimaView(CreateView):
    #Hay que replicar acá similar a la adquisición pero creando los objetos a la inversa, primero las materias primas y
    #la adquisición se crea vacía con la fecha actual
    """ model = MateriaPrima
    form_class = MateriaPrimaForm
    template_name = 'materia_prima/materia_prima_form.html'
    success_url = reverse_lazy('materia_prima:materia_prima_list')  # Cambia esto al nombre de tu URL
    success_message = "Se ha creado correctamente la materia prima."

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form) """

class ListMateriaPrimaView(ListView):
    model = MateriaPrima
    template_name = 'materia_prima/materia_prima_cat.html'
    context_object_name = 'materias_primas'
    #Hacer un query para mostrar solo la materias primas de un almacen si el usuario es almacenero, el almacen al que el pertenece

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

@login_required
def listMateriasPrimas(request):
    almacen_id = request.GET.get('almacen')
    producto_id = request.GET.get('producto')
    
    almacen = None
    if request.user.groups.filter(name='Almaceneros').exists():
        almacen = Almacen.objects.filter(responsable=request.user).first()

    materias_primas = Inv_Mat_Prima.objects.select_related('materia_prima', 'almacen')
    
    if request.user.groups.filter(name='Presidencia-Admin').exists() or request.user.is_staff:
        if almacen_id and almacen_id != 'todos':
            materias_primas = materias_primas.filter(almacen=almacen_id)
    else:
        if almacen:
            materias_primas = materias_primas.filter(almacen=almacen)
        else:
            materias_primas = Inv_Mat_Prima.objects.none()

    if producto_id:
        materias_primas = materias_primas.filter(materia_prima=producto_id)

    materias_primas = materias_primas.order_by('materia_prima__nombre', 'almacen__nombre')
    almacenes = Almacen.objects.all()
    productos = MateriaPrima.objects.all()
    total_productos = materias_primas.count()

    context = {
        'materias_primas':materias_primas,
        'almacenes':almacenes,
        'productos':productos,
        'almacen_id':almacen_id,
        'producto_id':producto_id,
        'almacen':almacen,
        'total_productos':total_productos,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'materia_prima/materia_prima_list.html', context)

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

class CreateImportCostoView(CreateView):
    model = MateriaPrima
    form_class = MateriaPrimaCostoForm
    template_name = 'materia_prima/import_costo_form.html'
    success_url = '/materia_prima/'
    success_message = "Se ha actualizado correctamente el costo de las materias primas."

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

                for data in imported_data:
                    nombre = str(data[1]).strip() if data[1] is not None else None  # Asegúrate de que sea un string
                    unidad = str(data[2]).strip() if data[2] is not None else None
                    concentracion = str(data[3]).strip() if data[3] is not None else None
                    conformacion = str(data[4]).strip() if data[4] is not None else None
                    costo = str(data[5]).strip() if data[5] is not None else None
                    tipo_materia_prima = str(data[6]).strip() if data[6] is not None else None
                    almacen = str(data[7]).strip() if data[7] is not None else None
                    cantidad = str(data[8]).strip() if data[8] is not None else None
                    print(data)                    
                    if not all([nombre, concentracion,  conformacion, unidad, costo, almacen, cantidad]):
                        print(f"Fila {No_fila + 1}: Todos los campos son obligatorios.")
                        messages.error(request, f"Fila {No_fila + 1}: Todos los campos son obligatorios.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    if len(nombre) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: El nombre de la materia prima no puede exceder 255 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    if len(unidad) > 10:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: La unidad de medida no puede exceder 10 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    if len(conformacion) > 50:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: La conformación no puede exceder 50 caracteres.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    if not concentracion.isdigit() or int(concentracion) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: 'Concentración' debe ser un número entero mayor que cero.")
                        return redirect('materia_prima:importarMateriasPrimas')
                    
                    if not re.match(r'^-?\d+(\.\d+)?$', costo) or float(costo) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: 'Costo' debe ser un número decimal válido mayor que cero.")
                        return redirect('materia_prima:importarMateriasPrimas')

                    almacen_obj = Almacen.objects.filter(nombre__iexact=almacen).first()
                    if almacen_obj is None:
                        print("No existe el almacen")
                        messages.error(request,
                                       f"Fila {No_fila}: No existe el almacén  '{str(data[7]).strip()}' en el nomenclador")
                        return redirect('importarProducto')
                    else:
                        print(f"Almacen {almacen_obj.nombre}")

                    costo = float(costo)  # Convertimos a entero después de la validación
                    concentracion = int(concentracion)  # Convertimos a entero después de la validación
                    
                    try:
                        materia_prima, created_mp = MateriaPrima.objects.update_or_create(                    
                            nombre=nombre,
                            defaults={
                            'unidad_medida': unidad,
                            'tipo_materia_prima' : tipo_materia_prima,
                            'conformacion' : conformacion,
                            'concentracion' : concentracion,
                            'costo' : costo,
                            }
                        )

                        materia_prima.clean()  # Valida los datos antes de guardar
                        materia_prima.save()

                        #Ahora a actualizar inventario
                        inventario_mp, created_inv = Inv_Mat_Prima.objects.get_or_create(
                            materia_prima=materia_prima, almacen=almacen_obj)
                        if created_inv:
                            print('Creado inventario')
                            fecha_actual = datetime.now()
                            fecha_codigo = fecha_actual.strftime('%y%m%d')
                        else:
                            print('No fue ceado el inventario')
                            print(inventario_mp.almacen)
                        """ if cantidad > inventario_prod.cantidad:
                            vale.entrada = True 
                            mov.cantidad = cantidad - inventario_prod.cantidad
                        else:
                            vale.entrada = False
                            mov.cantidad = inventario_prod.cantidad - cantidad
                        vale.save()
                        mov.save() """
                        inventario_mp.cantidad = decimal.Decimal(cantidad)
                        print(inventario_mp.cantidad)
                        inventario_mp.save()
                        print(inventario_mp.materia_prima)

                        No_fila += 1 # Incrementa solo si se guarda correctamente
                        

                    except Exception as e:
                        print(f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('materia_prima:importarMateriasPrimas')

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(materia_existentes)
                    print(f'Se han importado {Total_filas} materias primas satisfactoriamente.')
                    messages.success(request, f'Se han importado {Total_filas} materias primas satisfactoriamente.')
                    if materia_existentes:
                        print('Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             materia_existentes))
                        messages.warning(request,
                                         'Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             materia_existentes))
                        return redirect('materia_prima:importarMateriasPrimas')

                else:
                    if materia_existentes:
                        print('Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             materia_existentes))
                        messages.warning(request,
                                         'Las siguientes materias primas ya se encontraban registradas: ' + ', '.join(
                                             materia_existentes))
                        return redirect('materia_prima:importarMateriasPrimas')
                    else:
                        print("No se importó ninguna materia prima.")
                        messages.warning(request, "No se importó ningúna materia prima.")
                        return redirect('materia_prima:importarMateriasPrimas')

                return redirect('materia_prima:materia_prima_list')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('materia_prima:materia_prima_list')
    return render(request, 'materia_prima/import_form.html')

def importarCosto(request):
    if request.method == 'POST':
        file = request.FILES.get('excel')
        No_fila = 0
        materia_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('updateCostoMateriasPrimas')

        try:
            with (transaction.atomic()):
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                print(f"Importada: {imported_data}")    
                for data in imported_data:
                    print(f"En el for{str(data[1])}")
                    nombre = str(data[0]).strip() if data[0] is not None else None  # Asegúrate de que sea un string
                    costo = str(data[1]).strip() if data[1] is not None else None

                    print(f"nombre: {nombre}")
                    print(f"costo: {costo}")

                    if not all([nombre, costo]):
                        print(f"Fila {No_fila + 2}: Todos los campos son obligatorios.")
                        messages.error(request, f"Fila {No_fila + 2}: Todos los campos son obligatorios.")
                        return redirect('materia_prima:updateCostoMateriasPrimas')

                    if len(nombre) > 255:
                        print(f"Fila {No_fila + 2}: El nombre de la materia prima no puede exceder 255 caracteres.")
                        messages.error(request,
                                       f"Fila {No_fila + 2}: El nombre de la materia prima no puede exceder 255 caracteres.")
                        return redirect('materia_prima:updateCostoMateriasPrimas')

                    if not re.match(r'^-?\d+(\.\d+)?$', costo) or float(costo) <= 0:
                        print(f"Fila {No_fila + 2}: 'Costo' debe ser un número decimal válido mayor que cero.")
                        messages.error(request,
                                       f"Fila {No_fila + 2}: 'Costo' debe ser un número decimal válido mayor que cero.")
                        return redirect('materia_prima:updateCostoMateriasPrimas')

                    costo = float(costo)  # Convertimos a entero después de la validación
                    print(costo)
                    try:
                        materia_prima = MateriaPrima.objects.filter(nombre=nombre)
                        if not materia_prima:
                            print(f"No se encontró la materia prima de la {No_fila + 1}")
                        else:    
                            materia_prima[0].costo = costo
                            materia_prima[0].save()
                            print("Guardada")
                            No_fila += 1 # Incrementa solo si se guarda correctamente
                        

                    except Exception as e:
                        print(f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('materia_prima:updateCostoMateriasPrimas')

                # Mensajes finales
                print(No_fila)
                if No_fila > 0:
                    Total_filas = No_fila
                    messages.success(request, f'Se ha actualizado el costo de {Total_filas} materias primas satisfactoriamente.')
                else:
                    messages.warning(request, "No se importó actualizó ningún costo")
                    return redirect('materia_prima:updateCostoMateriasPrimas')

                return redirect('materia_prima:materia_prima_list')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('materia_prima:materia_prima_list')
    return render(request, 'materia_prima/import_costo_form.html')



###Gestionar Tipos de MP

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