# views.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
import datetime
import json
# formtools.wizard.views import SessionWizardView
from collections import OrderedDict
from .models import Produccion
from materia_prima.models import MateriaPrima
from inventario.models import Inv_Mat_Prima
from nomencladores.almacen.models import Almacen
from .forms import ProduccionForm, MateriaPrimaForm

class ProduccionListView(ListView):
    model = Produccion
    template_name = 'produccion/list.html'
    context_object_name = 'produccions'

class ProduccionDeleteView(DeleteView):
    model = Produccion
    template_name = 'produccion/confirm_delete.html'
    success_url = reverse_lazy('produccion_list')

@method_decorator(csrf_exempt, name='dispatch')
class CrearProduccionView(View):
    template_name = 'produccion/crear_produccion.html'
    
    def get(self, request):
        produccion_form = ProduccionForm()
        materia_prima_form = MateriaPrimaForm()
        
        # Inicializar sesión si no existe
        if 'produccion_data' not in request.session:
            request.session['produccion_data'] = {}
        
        context = {
            'produccion_form': produccion_form,
            'materia_prima_form': materia_prima_form,
            'materias_primas_json': self.get_materias_primas_json(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        step = request.POST.get('step')
        
        if step == '1':
            return self.procesar_paso_1(request)        
        elif step == '2':
            return self.procesar_paso_2(request)
        else:
            return JsonResponse({'success': False, 'errors': 'Paso no válido'})
    
    def procesar_paso_1(self, request):
        """Guardar solo los valores primitivos en sesión"""
        produccion_form = ProduccionForm(request.POST)
        if produccion_form.is_valid():
            # Extraer solo datos primitivos para la sesión
            session_data = {
                'lote': request.POST.get('lote'),
                'nombre_producto': request.POST.get('nombre_producto'),
                'cantidad_estimada': request.POST.get('cantidad_estimada'),
                'costo': request.POST.get('costo'),
                'pruebas_quimicas': request.POST.get('pruebas_quimicas'),
                'planta_id': request.POST.get('planta'),  # Guardar el ID como string
            }
            
            # Guardar en sesión
            request.session['produccion_data'] = session_data
            request.session.modified = True
            print("Datos sesion 1: ", request.session['produccion_data'])
            return JsonResponse({'success': True, 'step': 2})
        else:
            return JsonResponse({'success': False, 'errors': produccion_form.errors})
    
    def procesar_paso_2(self, request):
        # Recuperar datos del paso 1 de la sesión
        
        produccion_data = request.session.get('produccion_data', {})
        
        print("Datos en sesión 2:", produccion_data)  # Para debug
        
        if not produccion_data:
            return JsonResponse({
                'success': False, 
                'errors': 'Datos de producción no encontrados. Por favor, complete el paso 1 nuevamente.'
            })
            
        
        # Verificar que los datos mínimos estén presentes
        required_fields = ['lote', 'nombre_producto', 'cantidad_estimada', 'costo', 'planta_id']
        missing_fields = [field for field in required_fields if not produccion_data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False, 
                'errors': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            })
        
        # Procesar materias primas
        materias_primas = self.procesar_materias_primas(request.POST)
        
        if not materias_primas:
            return JsonResponse({'success': False, 'errors': 'Debe agregar al menos una materia prima'})
        
        try:
            # Obtener la instancia de Planta
            from .models import Planta
            planta_instance = Planta.objects.get(id=produccion_data['planta_id'])
            
            # Guardar producción
            produccion = Produccion.objects.create(
                lote=produccion_data['lote'],
                nombre_producto=produccion_data['nombre_producto'],
                cantidad_estimada=produccion_data['cantidad_estimada'],
                costo=produccion_data['costo'],
                pruebas_quimicas=produccion_data.get('pruebas_quimicas', ''),
                planta=planta_instance,
                estado='pendiente'
            )
            
            # Guardar materias primas
            for mp_data in materias_primas:
                Inv_Mat_Prima.objects.create(
                    #produccion=produccion,
                    materia_prima=mp_data['materia_prima'],
                    almacen=mp_data['almacen'],
                    cantidad=mp_data['cantidad']
                )
            
            # Limpiar sesión
            if 'produccion_data' in request.session:
                del request.session['produccion_data']
                request.session.modified = True
            
            return JsonResponse({
                'success': True, 
                'message': 'Producción creada exitosamente', 
                'produccion_id': produccion.id,
                'redirect_url': reverse('produccion_list')  # Ajusta esta URL
            })
            
        except Planta.DoesNotExist:
            return JsonResponse({'success': False, 'errors': 'La planta seleccionada no existe'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': f'Error al guardar: {str(e)}'})

    def get_materias_primas_json(self):
        materias_primas = MateriaPrima.objects.all().values(
            'id', 'nombre', 'tipo_materia_prima', 'conformacion', 'unidad_medida', 'concentracion', 'costo'
        )
        return list(materias_primas)
    
    def procesar_materias_primas(self, post_data):
        materias_primas = []
        i = 0
        
        while f'materias_primas[{i}][materia_prima]' in post_data:
            materia_prima_id = post_data.get(f'materias_primas[{i}][materia_prima]')
            cantidad = post_data.get(f'materias_primas[{i}][cantidad]')
            almacen_id = post_data.get(f'materias_primas[{i}][almacen]')
            
            if materia_prima_id and cantidad and almacen_id:
                try:
                    materia_prima = MateriaPrima.objects.get(id=materia_prima_id)
                    almacen = Almacen.objects.get(id=almacen_id)
                    
                    materias_primas.append({
                        'materia_prima': materia_prima,
                        'cantidad': cantidad,
                        'almacen': almacen
                    })
                except (MateriaPrima.DoesNotExist, Almacen.DoesNotExist):
                    pass
            
            i += 1
        
        return materias_primas

def get_materias_primas_data(request):
    """API para obtener datos de materias primas en JSON"""
    materias_primas = MateriaPrima.objects.all().values(
        'id', 'nombre', 'tipo', 'conformacion', 'unidad_medida', 'concentracion', 'costo'
    )
    return JsonResponse(list(materias_primas), safe=False)

#Este es el que está en uso
def iniciar_produccion(request, pk):
    """View para iniciar una producción específica"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.estado == 'pendiente':
        produccion.estado = 'En proceso'
        produccion.save()
        messages.success(request, f'✅ Producción {produccion.lote} iniciada correctamente')
    else:
        messages.warning(request, f'⚠️ La producción {produccion.lote} ya está en estado: {produccion.estado}')
    
    return redirect('produccion_list')
#Este dió error
class CambiarEstadoProduccionView(View):
    def post(self, request, pk):
        produccion_p = get_object_or_404(Produccion, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado:
            estado_anterior = produccion_p.estado
            produccion_p.estado = nuevo_estado
            produccion_p.save()
            
            messages.success(request, f'Estado cambiado de {estado_anterior} a {nuevo_estado}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'estado_actual': produccion_p.estado,
                    'mensaje': f'Estado cambiado exitosamente a {nuevo_estado}'
                })
        
        return redirect('produccion_list')

""" class ProduccionUpdateView(UpdateView):
    model = Produccion
    form_class = ProduccionForm
    template_name = 'produccion/form.html'
    success_url = reverse_lazy('produccion_list') """

def concluir_produccion(request, pk):
    """View para mostrar formulario de conclusión"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if request.method == 'POST' and produccion.estado == 'En proceso':
        cantidad_real = request.POST.get('cantidad_real')
        
        if cantidad_real:
            try:
                cantidad_real = float(cantidad_real)
                if cantidad_real > 0:
                    produccion.cantidad_real = cantidad_real
                    produccion.estado = 'Terminada'
                    produccion.fecha_actualizacion = datetime.datetime.now()
                    produccion.save()
                    
                    messages.success(request, f'✅ Producción {produccion.lote} completada. Cantidad obtenida: {cantidad_real}')
                    return redirect('produccion_list')
                else:
                    messages.error(request, '❌ La cantidad real debe ser mayor a 0')
            except ValueError:
                messages.error(request, '❌ La cantidad debe ser un número válido')
        else:
            messages.error(request, '❌ Debe especificar la cantidad obtenida')
    
    return render(request, 'produccion/concluir_produccion.html', {
        'produccion': produccion
    })