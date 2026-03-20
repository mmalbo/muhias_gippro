from datetime import datetime
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from envase_embalaje.forms import EnvaseEmbalajeForm, EnvaseEmbalajeUpdateForm
from envase_embalaje.models import EnvaseEmbalaje
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from nomencladores.almacen.models import Almacen
from inventario.models import Inv_Envase
from envase_embalaje.formato.models import Formato
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse, Http404
import re
import decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from tablib import Dataset

# Create your views here.

class ListEnvaseEmbalajeView(LoginRequiredMixin, ListView):
    model = EnvaseEmbalaje
    template_name = 'envase_embalaje/envase_cat.html'
    context_object_name = 'envase_embalaje'
    #Hacer un query para mostrar solo los envases de un almacen si el usuario es almacenero, el almacen al que el pertenece

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
def listEnvaseEmbalaje(request):
    almacen_id = request.GET.get('almacen')
    producto_id = request.GET.get('producto')
    
    almacen = None
    if request.user.groups.filter(name='Almaceneros').exists():
        almacen = Almacen.objects.filter(responsable=request.user).first()

    envase_embalaje = Inv_Envase.objects.select_related('envase', 'almacen')
    
    if request.user.groups.filter(name='Presidencia-Admin').exists() or request.user.is_staff:
        if almacen_id and almacen_id != 'todos':
            envase_embalaje = envase_embalaje.filter(almacen=almacen_id)
    else:
        if almacen:
            envase_embalaje = envase_embalaje.filter(almacen=almacen)
        else:
            envase_embalaje = Inv_Envase.objects.none()

    if producto_id:
        envase_embalaje = envase_embalaje.filter(envase=producto_id)

    envase_embalaje = envase_embalaje.order_by('envase__codigo_envase', 'almacen__nombre')
    almacenes = Almacen.objects.all()
    productos = EnvaseEmbalaje.objects.all()
    total_productos = envase_embalaje.count()

    print(envase_embalaje)

    context = {
        'envase_embalaje':envase_embalaje,
        'almacenes':almacenes,
        'productos':productos,
        'almacen_id':almacen_id,
        'producto_id':producto_id,
        'almacen':almacen,
        'total_productos':total_productos,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'envase_embalaje/envase_list.html', context)

class UpdateEnvaseEmbalajeView(LoginRequiredMixin, UpdateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeUpdateForm
    template_name = 'envase_embalaje/envase_embalaje_form.html'
    success_url = reverse_lazy('envase_embalaje_lista')  # Cambia esto al nombre de tu URL

    def form_valid(self, form):
        messages.success(self.request, "Se ha actualizado correctamente el envase o embalaje.")
        return super().form_valid(form)

    """ def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.get('instance')
        if instance:
            kwargs['initial'] = {
                'ficha_tecnica': instance.get_ficha_tecnica_name,
                'hoja_seguridad': instance.get_hoja_seguridad_name,
            }
        return kwargs """

    """ def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        # context['factura_adquisicion_nombre'] = basename(obj.factura_adquisicion.name) if obj.factura_adquisicion else ''
        context['ficha_tecnica_nombre'] = basename(obj.ficha_tecnica.name) if obj.ficha_tecnica else ''
        context['hoja_seguridad_nombre'] = basename(obj.hoja_seguridad.name) if obj.hoja_seguridad else ''
        return context """

class DeleteEnvaseEmbalajeView(LoginRequiredMixin, DeleteView):
    model = EnvaseEmbalaje
    template_name = 'envase_embalaje/envase_embalaje_confirm_delete.html'
    success_url = reverse_lazy('envase_embalaje_list')  # Cambia esto al nombre de tu URL

@login_required
def get_envase_embalaje(request, pk):
    try:
        almacen = Almacen.objects.get(pk=pk)
        envases_embalajes = almacen.envase_embalaje.all()
        envase_embalaje_data = [{'nombre': envase_embalaje.codigo_envase, 'nombre_almacen': almacen.nombre} for envase_embalaje in
                                envases_embalajes]

        return JsonResponse(envase_embalaje_data, safe=False)
    except Almacen.DoesNotExist:
        raise Http404("Envase o embalaje no encontrado")

@login_required
def detalle_envase(request, pk):
    """Ver detalle completo de un parámetro"""
    envase = get_object_or_404(EnvaseEmbalaje, id=pk)
    
    return render(request, 'envase_embalaje\detalle_envase_embalaje.html', {
        'envase': envase,
    })


class CreateImportView(LoginRequiredMixin, CreateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeForm
    template_name = 'envase_embalaje/import_form.html'
    success_url = '/envase_embalaje/'
    success_message = "Se ha importado correctamente el envase o embalaje."

class EnvaseEmbalajeCreateView(LoginRequiredMixin, CreateView):
    model = EnvaseEmbalaje
    form_class = EnvaseEmbalajeForm
    template_name = 'envase_embalaje/form.html'
    success_url = reverse_lazy('envase_embalaje_lista')
    success_message = "Se ha creado correctamente el almacén."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['almacenes'] = EnvaseEmbalaje.objects.all()
        return context

@login_required
def importar(request):
    print("En importar")
    if request.method == 'POST':
        print("En el post")
        file = request.FILES.get('excel')
        No_fila = 0
        envases_existentes = []

        if not (file and (file.name.endswith('.xls') or file.name.endswith('.xlsx'))):
            messages.error(request, 'La extensión del archivo no es correcta, debe ser .xls o .xlsx')
            return redirect('envase_embalaje:importarEnvaseEmbalaje')

        try:
            print("En try")
            with (transaction.atomic()):
                format = 'xls' if file.name.endswith('.xls') else 'xlsx'
                imported_data = Dataset().load(file.read(), format=format)
                
                for data in imported_data:
                    # Verificar cuántas columnas tiene la fila
                    if len(data) < 7:  # Necesitas al menos 7 columnas
                        messages.error(request, f"Fila {No_fila+1}: El archivo debe tener al menos 9 columnas. Tiene {len(data)} columnas.")
                        return redirect('importarEnvaseEmbalaje')
                    print(f"En importar: {data}")
                    nombre = str(data[1]).strip() if data[1] is not None else None  # Asegúrate de que sea un string
                    tipo = str(data[2]).strip() if data[2] is not None else None
                    formato = str(data[3]).strip() if data[3] is not None else None
                    proveedor = str(data[4]).strip() if data[4] is not None else None
                    costo = str(data[5]).strip() if data[5] is not None else None
                    cantidad = str(data[6]).strip() if data[6] is not None else None
                    almacen = str(data[7]).strip() if data[7] is not None else None

                    print(f"Nombre: {nombre}")

                    if not all([nombre, costo, almacen]):
                        print(f"Fila {No_fila + 1}: Estos campos son obligatorios.")
                        messages.error(request, f"Fila {No_fila + 1}: Todos los campos son obligatorios.")
                        return redirect('importarEnvaseEmbalaje')

                    if len(nombre) > 255:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: El nombre del envase no puede exceder 255 caracteres.")
                        return redirect('importarEnvaseEmbalaje')
                    
                    if not re.match(r'^-?\d+(\.\d+)?$', costo) or float(costo) <= 0:
                        messages.error(request,
                                       f"Fila {No_fila + 1}: 'Costo' debe ser un número decimal válido mayor que cero.")
                        return redirect('importarEnvaseEmbalaje')

                    print(f"Validaciones listas")
                    
                    tipo_obj = TipoEnvaseEmbalaje.objects.filter(nombre__iexact=tipo).first()
                       
                    if tipo_obj is None:
                        print("No existe el tipo"+tipo)
                        messages.error(request,
                                       f"Fila {No_fila}: No existe el tipo de envase  '{str(data[3]).strip()}' en el nomenclador")
                        return redirect('importarEnvaseEmbalaje')
                    else:
                        print(f"Tipo: {tipo_obj.nombre}")

                    if formato:
                        cap_str = ''
                        for j in formato:
                            try:
                                if int(j) or j == '0':
                                    cap_str = cap_str + j
                                else:
                                    break
                            except:
                                break

                        if cap_str == '':
                            capacidad = 0
                        else:
                            capacidad = int(cap_str)
                        if 'kg' in formato.lower():
                            um = 'KG'
                        elif 'ml' in formato.lower():
                            um = 'ML'
                        elif 'l' in formato.lower():
                            um = 'L'
                        elif 'granel' in formato.lower():
                            capacidad = 0
                            um = 'L'
                        else:
                            um = 'U'

                        print(f"UM: {um} capacidad: {capacidad}")

                        formato_o = Formato.objects.filter(unidad_medida=um, capacidad=capacidad).first()
                        if not formato_o:
                            formato_o = Formato.objects.create(unidad_medida=um, capacidad=capacidad)
                        print(f"Formato: {formato_o}")

                    almacen_obj = Almacen.objects.filter(nombre__iexact=almacen).first()
                    if almacen_obj is None:
                        print("No existe el almacen")
                        messages.error(request,
                                       f"Fila {No_fila}: No existe el almacén  '{str(data[7]).strip()}' en el nomenclador")
                        return redirect('importarEnvaseEmbalaje')
                    else:
                        print(f"Almacen {almacen_obj.nombre}")

                    costo = float(costo)  # Convertimos a entero después de la validación
                    
                    if not cantidad:
                        cantidad = 0
                    
                    try:
                        if formato: 
                            envase_emb, created_ee = EnvaseEmbalaje.objects.update_or_create(                    
                                nombre=nombre,
                                defaults={
                                    'tipo_envase_embalaje': tipo_obj,
                                    'formato' : formato_o,
                                    'proveedor' : proveedor,
                                    'estado' : 'en_almacen',
                                    'costo' : costo,
                                }
                            )
                        else:
                            envase_emb, created_ee = EnvaseEmbalaje.objects.update_or_create(                    
                                nombre=nombre,
                                defaults={
                                    'tipo_envase_embalaje': tipo_obj,
                                    'proveedor' : proveedor,
                                    'estado' : 'en_almacen',
                                    'costo' : costo,
                                }
                            )

                        #envase_emb.save()
                        print("Codigo nuevo"+str(envase_emb.codigo_envase))

                        #Ahora a actualizar inventario
                        inventario_ee, created_inv = Inv_Envase.objects.get_or_create(
                            envase=envase_emb, almacen=almacen_obj)
                        if created_inv:
                            print('Creado inventario')
                            fecha_actual = datetime.now()
                            fecha_codigo = fecha_actual.strftime('%y%m%d')
                        else:
                            print('No fue creado el inventario')
                            print(inventario_ee.almacen)
                        
                        inventario_ee.cantidad = decimal.Decimal(cantidad)
                        print(inventario_ee.cantidad)
                        inventario_ee.save()
                        print(inventario_ee.envase)

                        No_fila += 1 # Incrementa solo si se guarda correctamente
                        

                    except Exception as e:
                        print(f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        messages.error(request, f"Error al procesar la fila {No_fila + 2}: {str(e)}")
                        return redirect('importarEnvaseEmbalaje')

                # Mensajes finales
                if No_fila > 0:
                    Total_filas = No_fila - len(envases_existentes)
                    print(f'Se han importado {Total_filas} envases o embalajes satisfactoriamente.')
                    messages.success(request, f'Se han importado {Total_filas} envases o embalajes satisfactoriamente.')
                    if envases_existentes:
                        print('Los siguientes envases o embalajes ya se encontraban registradas: ' + ', '.join(
                                             envases_existentes))
                        messages.warning(request,
                                         'Los siguientes envases o embalajes ya se encontraban registradas: ' + ', '.join(
                                             envases_existentes))
                        return redirect('importarEnvaseEmbalaje')

                else:
                    if envases_existentes:
                        print('Los siguientes envases o embalajes ya se encontraban registradas: ' + ', '.join(
                                             envases_existentes))
                        messages.warning(request,
                                         'Los siguientes envases o embalajes ya se encontraban registradas: ' + ', '.join(
                                             envases_existentes))
                        return redirect('importarEnvaseEmbalaje')
                    else:
                        print("No se importó ningun envases o embalajes .")
                        messages.warning(request, "No se importó ningun envases o embalajes .")
                        return redirect('importarEnvaseEmbalaje')

                return redirect('list_envase_embalaje')

        except Exception as e:
            messages.error(request, f"Ocurrió un error durante la importación: {str(e)}")
            return redirect('list_envase_embalaje')
    return render(request, 'envase_embalaje/import_form.html')
