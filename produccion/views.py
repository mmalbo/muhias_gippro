# views.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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

class ProduccionUpdateView(UpdateView):
    model = Produccion
    form_class = ProduccionForm
    template_name = 'produccion/form.html'
    success_url = reverse_lazy('produccion_list')

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

""" class ProduccionCreateView(CreateView):
    model = Produccion
    form_class = ProduccionForm
    template_name = 'produccion/form.html'
    success_url = reverse_lazy('produccion_list') 
# Configuración de almacenamiento temporal
TMP_Almac = os.path.join(settings.BASE_DIR, 'tmp_wizard')
if not os.path.exists(TMP_Almac):
    os.makedirs(TMP_Almac)
file_alm = FileSystemStorage(location=TMP_Almac)

class ProduccionWizard(SessionWizardView):
    file = file_alm
    # Diccionario que mapea cada paso con su template
    template_dict = {
        'datos': 'produccion/datos_form.html',
        'materias': 'produccion/materias_form.html',  # Para todos los pasos materia_*
    }
    
    ## Debemos revisarlo
    def get_template_names(self):
        Determina qué plantilla usar para el paso actual
        current_step = self.steps.current
        
        # Para pasos conocidos, usa su template específico
        if current_step in self.template_dict:
            return [self.template_dict[current_step]]
        
        # Fallback por defecto
        return ['produccion/wizard_base.html']

    form_list = [
        ('produccion', ProduccionForm),
        ('cantidad', Inv_MP_Form),
    ]

    def get_form_list(self):
        Versión robusta que siempre retorna al menos los formularios base
        form_list = OrderedDict(self.form_list)        
       
        return form_list
    
    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # Para los pasos de materia prima, intentar mantener la selección previa
        if step.startswith('materia'):
            prev_data = self.get_cleaned_data_for_step(step)
            if prev_data:
                initial.update(prev_data)
        
        return initial
    
    def get_form(self, step=None, data=None, files=None):
        # Asegurar que siempre haya una lista de formularios
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('produccion', ProduccionForm),
                ('cantidad', Inv_MP_Form),
            ])
        
        if step is None:
            step = self.steps.current
        try:
            form_class = form_list[step]
            return form_class(data=data, files=files, prefix=self.get_form_prefix(step, form_class))
        except KeyError:
            # Si el paso no existe, redirigir al primer paso
            self.storage.current_step = 'produccion'
            form_class = form_list['produccion']
            return form_class(data=data, files=files, prefix=self.get_form_prefix('produccion', form_class))
    
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        
        # Asegurar que siempre tengamos una lista de pasos
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('produccion', ProduccionForm),
                ('cantidad', Inv_MP_Form),
            ])

        Añadir información específica del paso
        current_step = self.steps.current
        context['step_title'] = {
                'produccion': 'Información General',
                'cantidad': 'Cantidad de Materias Primas necesarias'
            }.get(current_step, 'Paso del Proceso')
        
        Calcular progreso
        step_index = list(form_list.keys()).index(self.steps.current)
        context.update({
            'step_number': step_index + 1,
            'total_steps': len(form_list),
            'step_title': self.get_step_title(),
            'form_list_keys': list(form_list.keys()),
        })
        
        return context
    
    def get_step_title(self):
        titles = {
            'produccion': 'Información General',
            'cantidad': 'Cantidad de Materias Primas necesarias',
        }

        return titles.get(self.steps.current, "Paso del Proceso")
    
    def done(self, form_list, **kwargs):
        Procesamiento seguro de los datos
        try:
            produccion_data = [f for f in form_list if isinstance(f, ProduccionForm)][0].cleaned_data
            cantidad_data = [f for f in form_list if isinstance(f, Inv_MP_Form)][0].cleaned_data
            
            Crear Produccion
            datos_prod = Produccion.objects.create(
                lote=produccion_data['lote'],
                nombre_producto=produccion_data['nombre_producto'],
                cantidad_estimada=produccion_data['cantidad_estimada'],
                costo=produccion_data['costo'],
                planta=produccion_data['planta']
            )
            
            Procesar materias primas
            materia_forms = [f for f in form_list if isinstance(f, Inv_MP_Form)]
            for form in materia_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                materia = Inv_MP_Form.objects.create(
                        lote_prod=datos_prod,
                        inv_materia_prima=data['inv_materia_prima'],
                        cantidad_materia_prima=data['cantidad_materia_prima'],
                    )      
            
            Limpiar almacenamiento
            self.storage.reset()
            return redirect('produccion_list')
        
        except Exception as e:
            print(f"Error al procesar la solicitud de producción: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')"""

    