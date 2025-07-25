from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from formtools.wizard.views import SessionWizardView
from .forms import CompraForm, CantidadMateriasForm, MateriaPrimaForm, CantidadEnvasesForm, EnvasesForm, InsumosForm, CantidadInsumosForm
from .models import Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
#from django.views.generic.edit import CreateView
from django.http import JsonResponse
from collections import OrderedDict
from django.conf import settings
from django.forms.models import modelform_factory
from django import forms
import os
from django.views import View
from django.contrib import messages
from django.db.models import Count

### Incorporar envases...

# Configuración de almacenamiento temporal
TMP_STORAGE = os.path.join(settings.BASE_DIR, 'tmp_wizard')
if not os.path.exists(TMP_STORAGE):
    os.makedirs(TMP_STORAGE)
file_storage = FileSystemStorage(location=TMP_STORAGE)

# Para las maerias primas
class CompraWizard(SessionWizardView):
    file_storage = file_storage
    # Diccionario que mapea cada paso con su template
    template_dict = {
        'compra': 'adquisicion/compra_form.html',
        'cantidad': 'adquisicion/cantidad_form.html',
        'materia': 'adquisicion/materia_form.html',  # Para todos los pasos materia_*
    }

    def get_template_names(self):
        """Determina qué plantilla usar para el paso actual"""
        current_step = self.steps.current
        
        # Si es un paso de materia prima, usa el template genérico
        if current_step.startswith('materia_'):
            return [self.template_dict['materia']]
        
        # Para pasos conocidos, usa su template específico
        if current_step in self.template_dict:
            return [self.template_dict[current_step]]
        
        # Fallback por defecto
        return ['adquisicion/wizard_base.html']

    form_list = [
        ('compra', CompraForm),
        ('cantidad', CantidadMateriasForm),
    ]

    def get_form_list(self):
        """Versión robusta que siempre retorna al menos los formularios base"""
        form_list = OrderedDict(self.form_list)
        
        # Agregar pasos dinámicos si hay datos de cantidad
        try:
            cantidad_data = self.storage.get_step_data('cantidad')
            if cantidad_data and 'cantidad-cantidad' in cantidad_data:
                num_materias = int(cantidad_data['cantidad-cantidad'][0])
                for i in range(num_materias):
                    form_list[f'materia_{i}'] = MateriaPrimaForm
        except (KeyError, ValueError, TypeError):
            pass
        return form_list
    
    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # Para los pasos de materia prima, intentar mantener la selección previa
        if step.startswith('materia_'):
            prev_data = self.get_cleaned_data_for_step(step)
            if prev_data:
                initial.update(prev_data)
        
        return initial

    
    def get_form(self, step=None, data=None, files=None):
        # Asegurar que siempre haya una lista de formularios
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('compra', CompraForm),
                ('cantidad', CantidadMateriasForm),
            ])
        
        if step is None:
            step = self.steps.current
        try:
            form_class = form_list[step]
            return form_class(data=data, files=files, prefix=self.get_form_prefix(step, form_class))
        except KeyError:
            # Si el paso no existe, redirigir al primer paso
            self.storage.current_step = 'compra'
            form_class = form_list['compra']
            return form_class(data=data, files=files, prefix=self.get_form_prefix('compra', form_class))
    
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        
        # Asegurar que siempre tengamos una lista de pasos
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('compra', CompraForm),
                ('cantidad', CantidadMateriasForm),
            ])

        # Añadir información específica del paso
        current_step = self.steps.current
        if current_step.startswith('materia_'):
            materia_num = int(current_step.split('_')[1]) + 1
            context['step_title'] = f"Materia Prima {materia_num}"
        else:
            context['step_title'] = {
                'compra': 'Información General',
                'cantidad': 'Cantidad de Materias'
            }.get(current_step, 'Paso del Proceso')
        
        # Calcular progreso
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
            'compra': "Información General",
            'cantidad': "Cantidad de Materias",
        }
        
        if self.steps.current.startswith('materia_'):
            try:
                index = int(self.steps.current.split('_')[1]) + 1
                return f"Materia Prima {index}"
            except (ValueError, IndexError):
                return "Registro de Materia Prima"
        
        return titles.get(self.steps.current, "Paso del Proceso")
    
    def done(self, form_list, **kwargs):
        # Procesamiento seguro de los datos
        try:
            compra_data = [f for f in form_list if isinstance(f, CompraForm)][0].cleaned_data
            cantidad_data = [f for f in form_list if isinstance(f, CantidadMateriasForm)][0].cleaned_data
            
            # Crear compra
            compra = Adquisicion.objects.create(
                fecha_compra=compra_data['fecha_compra'],
                importada=compra_data['importada'],
                factura=compra_data['factura']
            )
            
            # Procesar materias primas
            materia_forms = [f for f in form_list if isinstance(f, MateriaPrimaForm)]
            for form in materia_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == MateriaPrimaForm.EXISTING:
                    materia = data['materia_existente']
                else:
                    materia = MateriaPrima.objects.create(
                        codigo=data['codigo'],
                        nombre=data['nombre'],
                        tipo_materia_prima=data['tipo_materia_prima'],
                        conformacion=data['conformacion'],
                        unidad_medida=data['unidad_medida'],
                        concentracion=data['concentracion'],
                        costo=data['costo'],
                        ficha_tecnica=data['ficha_tecnica'],
                        hoja_seguridad=data['hoja_seguridad'],
                    )
                
                DetallesAdquisicion.objects.create(
                    adquisicion=compra,
                    materia_prima=materia,
                    cantidad=data['cantidad'],
                    almacen=data['almacen']
                )
            
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compra_exitosa')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

from materia_prima.tipo_materia_prima.choices import CHOICE_TIPO

class MateriaPrimaDetalleView(View):
    def get(self, request, pk):
        try:
            materia = MateriaPrima.objects.get(pk=pk)
            return JsonResponse({
                'id': materia.codigo,
                'nombre': materia.nombre,
                'concentracion': materia.concentracion or '',
                'conformacion': materia.conformacion or '',
                'tipo': CHOICE_TIPO[int(materia.tipo_materia_prima.tipo)-1][1] or '',
                'medida': materia.unidad_medida or '',
            })
        except MateriaPrima.DoesNotExist:
            return JsonResponse({'error': 'Materia prima no encontrada'}, status=404)

# Para los envases y embalajes 
class CompraEnvaseWizard(SessionWizardView):
    file_storage = file_storage
    # Diccionario que mapea cada paso con su template
    template_dict = {
        'compra': 'adquisicion/compra_form.html',
        'cantidad': 'adquisicion/cantidad_form.html',
        'envase': 'adquisicion/envase_form.html',  # Para todos los pasos envase_*
    }

    def get_template_names(self):
        """Determina qué plantilla usar para el paso actual"""
        current_step = self.steps.current
        
        # Si es un paso de materia prima, usa el template genérico
        if current_step.startswith('envase_'):
            return [self.template_dict['envase']]
        
        # Para pasos conocidos, usa su template específico
        if current_step in self.template_dict:
            return [self.template_dict[current_step]]
        
        # Fallback por defecto
        return ['adquisicion/wizard_base.html']

    form_list = [
        ('compra', CompraForm),
        ('cantidad', CantidadEnvasesForm),
    ]

    def get_form_list(self):
        """Versión robusta que siempre retorna al menos los formularios base"""
        form_list = OrderedDict(self.form_list)
        
        # Agregar pasos dinámicos si hay datos de cantidad
        try:
            cantidad_data = self.storage.get_step_data('cantidad')
            if cantidad_data and 'cantidad-cantidad' in cantidad_data:
                num_envases = int(cantidad_data['cantidad-cantidad'][0])
                for i in range(num_envases):
                    form_list[f'envase_{i}'] = EnvasesForm
        except (KeyError, ValueError, TypeError):
            pass
        return form_list
    
    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # Para los pasos de envase, intentar mantener la selección previa
        if step.startswith('envase_'):
            prev_data = self.get_cleaned_data_for_step(step)
            if prev_data:
                initial.update(prev_data)
        
        return initial

    
    def get_form(self, step=None, data=None, files=None):
        # Asegurar que siempre haya una lista de formularios
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('compra', CompraForm),
                ('cantidad', CantidadEnvasesForm),
            ])
        
        if step is None:
            step = self.steps.current
        try:
            form_class = form_list[step]
            return form_class(data=data, files=files, prefix=self.get_form_prefix(step, form_class))
        except KeyError:
            # Si el paso no existe, redirigir al primer paso
            self.storage.current_step = 'compra'
            form_class = form_list['compra']
            return form_class(data=data, files=files, prefix=self.get_form_prefix('compra', form_class))
    
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        
        # Asegurar que siempre tengamos una lista de pasos
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('compra', CompraForm),
                ('cantidad', CantidadEnvasesForm),
            ])

        # Añadir información específica del paso
        current_step = self.steps.current
        if current_step.startswith('envase_'):
            envase_num = int(current_step.split('_')[1]) + 1
            context['step_title'] = f"Envase {envase_num}"
        else:
            context['step_title'] = {
                'compra': 'Información General',
                'cantidad': 'Cantidad de Envases'
            }.get(current_step, 'Paso del Proceso')
        
        # Calcular progreso
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
            'compra': "Información General",
            'cantidad': "Cantidad de Envases",
        }
        
        if self.steps.current.startswith('envase_'):
            try:
                index = int(self.steps.current.split('_')[1]) + 1
                return f"Envase {index}"
            except (ValueError, IndexError):
                return "Registro de Envases"
        
        return titles.get(self.steps.current, "Paso del Proceso")
    
    def done(self, form_list, **kwargs):
        # Procesamiento seguro de los datos
        try:
            compra_data = [f for f in form_list if isinstance(f, CompraForm)][0].cleaned_data
            cantidad_data = [f for f in form_list if isinstance(f, CantidadEnvasesForm)][0].cleaned_data
            
            # Crear compra
            compra = Adquisicion.objects.create(
                fecha_compra=compra_data['fecha_compra'],
                importada=compra_data['importada'],
                factura=compra_data['factura']
            )
            
            # Procesar materias primas
            envase_forms = [f for f in form_list if isinstance(f, EnvasesForm)]
            for form in envase_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == EnvasesForm.EXISTING:
                    envase = data['envase_existente']
                else:
                    envase = EnvaseEmbalaje.objects.create(
                        tipo_envase_embalaje=data['tipo_envase_embalaje'],
                        formato=data['formato'],
                        costo=data['costo'],
                    )
                
                DetallesAdquisicionEnvase.objects.create(
                    adquisicion=compra,
                    envase_embalaje=envase,
                    cantidad=data['cantidad'],
                    almacen=data['almacen']
                )
            
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compra_exitosa')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

class EnvaseDetalleView(View):
    def get(self, request, pk):
        try:
            envase = EnvaseEmbalaje.objects.get(pk=pk)
            format = str(envase.formato.capacidad) + ' ' + envase.formato.unidad_medida
            return JsonResponse({
                'codigo': envase.codigo_envase,
                'formato': format or '',
                'tipo': envase.tipo_envase_embalaje.nombre or '',
            })
        except EnvaseEmbalaje.DoesNotExist:
            return JsonResponse({'error': 'Envase no encontrado'}, status=404)

# Para los insumos
class CompraInsumoWizard(SessionWizardView):
    file_storage = file_storage
    # Diccionario que mapea cada paso con su template
    template_dict = {
        'compra': 'adquisicion/compra_form.html',
        'cantidad': 'adquisicion/cantidad_form.html',
        'insumo': 'adquisicion/insumo_form.html',  # Para todos los pasos insumo_*
    }

    def get_template_names(self):
        """Determina qué plantilla usar para el paso actual"""
        current_step = self.steps.current
        
        # Si es un paso de insumo, usa el template genérico
        if current_step.startswith('insumo_'):
            return [self.template_dict['insumo']]
        
        # Para pasos conocidos, usa su template específico
        if current_step in self.template_dict:
            return [self.template_dict[current_step]]
        
        # Fallback por defecto
        return ['adquisicion/wizard_base.html']

    form_list = [
        ('compra', CompraForm),
        ('cantidad', CantidadInsumosForm),
    ]

    def get_form_list(self):
        """Versión robusta que siempre retorna al menos los formularios base"""
        form_list = OrderedDict(self.form_list)
        
        # Agregar pasos dinámicos si hay datos de cantidad
        try:
            cantidad_data = self.storage.get_step_data('cantidad')
            if cantidad_data and 'cantidad-cantidad' in cantidad_data:
                num_insumos = int(cantidad_data['cantidad-cantidad'][0])
                for i in range(num_insumos):
                    form_list[f'insumo_{i}'] = InsumosForm
        except (KeyError, ValueError, TypeError):
            pass
        return form_list
    
    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # Para los pasos de insumo, intentar mantener la selección previa
        if step.startswith('insumo_'):
            prev_data = self.get_cleaned_data_for_step(step)
            if prev_data:
                initial.update(prev_data)
        
        return initial

    
    def get_form(self, step=None, data=None, files=None):
        # Asegurar que siempre haya una lista de formularios
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('compra', CompraForm),
                ('cantidad', CantidadInsumosForm),
            ])
        
        if step is None:
            step = self.steps.current
        try:
            form_class = form_list[step]
            return form_class(data=data, files=files, prefix=self.get_form_prefix(step, form_class))
        except KeyError:
            # Si el paso no existe, redirigir al primer paso
            self.storage.current_step = 'compra'
            form_class = form_list['compra']
            return form_class(data=data, files=files, prefix=self.get_form_prefix('compra', form_class))
    
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        
        # Asegurar que siempre tengamos una lista de pasos
        form_list = self.get_form_list()
        if not form_list:
            form_list = OrderedDict([
                ('compra', CompraForm),
                ('cantidad', CantidadInsumosForm),
            ])

        # Añadir información específica del paso
        current_step = self.steps.current
        if current_step.startswith('insumo_'):
            insumo_num = int(current_step.split('_')[1]) + 1
            context['step_title'] = f"Insumo {insumo_num}"
        else:
            context['step_title'] = {
                'compra': 'Información General',
                'cantidad': 'Cantidad de Insumos'
            }.get(current_step, 'Paso del Proceso')
        
        # Calcular progreso
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
            'compra': "Información General",
            'cantidad': "Cantidad de Insumos",
        }
        
        if self.steps.current.startswith('insumo_'):
            try:
                index = int(self.steps.current.split('_')[1]) + 1
                return f"Insumo {index}"
            except (ValueError, IndexError):
                return "Registro de Insumos"
        
        return titles.get(self.steps.current, "Paso del Proceso")
    
    def done(self, form_list, **kwargs):
        # Procesamiento seguro de los datos
        try:
            compra_data = [f for f in form_list if isinstance(f, CompraForm)][0].cleaned_data
            cantidad_data = [f for f in form_list if isinstance(f, CantidadInsumosForm)][0].cleaned_data
            
            # Crear compra
            compra = Adquisicion.objects.create(
                fecha_compra=compra_data['fecha_compra'],
                importada=compra_data['importada'],
                factura=compra_data['factura']
            )
            
            # Procesar insumos
            insumo_forms = [f for f in form_list if isinstance(f, InsumosForm)]
            for form in insumo_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == InsumosForm.EXISTING:
                    insumo = data['insumo_existente']
                else:
                    insumo = InsumosOtros.objects.create(
                        codigo=data['codigo'],
                        nombre=data['nombre'],
                        descripcion=data['descripcion'],
                    )
                
                DetallesAdquisicionInsumo.objects.create(
                    adquisicion=compra,
                    insumo=insumo,
                    cantidad=data['cantidad'],
                    almacen=data['almacen']
                )
            
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compra_exitosa')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

class InsumoDetalleView(View):
    def get(self, request, pk):
        try:
            insumo = InsumosOtros.objects.get(pk=pk)
            #format = str(envase.formato.capacidad) + ' ' + envase.formato.unidad_medida
            return JsonResponse({
                'codigo': insumo.codigo,
                'nombre': insumo.nombre or '',
                'descripcion': insumo.descripcion or '',
            })
        except InsumosOtros.DoesNotExist:
            return JsonResponse({'error': 'Insumo no encontrado'}, status=404)


def compra_exitosa(request):
    return render(request, 'adquisicion/exito.html')

def list_mp_adquisiciones(request, template_name="adquisicion/mp_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

def list_env_adquisiciones(request, template_name="adquisicion/env_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles_envases')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

def list_ins_adquisiciones(request, template_name="adquisicion/ins_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles_insumos')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

def list_detalles_mp_adquisicion(request, id, template_name="adquisicion/detalles_mp_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicion.objects.filter(adquisicion=id).order_by('almacen')
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, locals())

def list_detalles_env_adquisicion(request, id, template_name="adquisicion/detalles_env_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicionEnvase.objects.filter(adquisicion=id).order_by('almacen')
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, locals())

def list_detalles_ins_adquisicion(request, id, template_name="adquisicion/detalles_ins_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicionInsumo.objects.filter(adquisicion=id).order_by('almacen')
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, locals())