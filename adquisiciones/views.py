import os
import decimal
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from formtools.wizard.views import SessionWizardView
from .forms import (CompraForm, CantidadMateriasForm, MateriaPrimaForm, 
                    CantidadEnvasesForm, EnvasesForm, InsumosForm, CantidadInsumosForm, 
                    ProductosForm, CantidadProductosForm, CompraEditForm, DetalleFormSet,
                    DetalleEnvaseFormSet, DetalleInsumoFormSet, DetalleProductoFormSet)
from .models import (Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, 
                     DetallesAdquisicionInsumo, DetallesAdquisicionProducto)
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
from producto.models import Producto
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
#from django.views.generic.edit import CreateView
from django.http import JsonResponse
from collections import OrderedDict
from django.conf import settings
from django.forms.models import modelform_factory
from django import forms
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

# Configuración de almacenamiento temporal
TMP_STORAGE = os.path.join(settings.BASE_DIR, 'tmp_wizard')
if not os.path.exists(TMP_STORAGE):
    os.makedirs(TMP_STORAGE)
file_storage = FileSystemStorage(location=TMP_STORAGE)

# Para las materias primas
class CompraWizard(LoginRequiredMixin, SessionWizardView):
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
                factura=compra_data['factura'],
                tipo_adquisicion='mp',
                almacen=compra_data['almacen']
            )
            
            # Procesar materias primas
            materia_forms = [f for f in form_list if isinstance(f, MateriaPrimaForm)]
            for form in materia_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == MateriaPrimaForm.EXISTING:
                    materia = data['materia_existente']

                    # Actualizar costo si se proporcionó uno nuevo
                    nuevo_costo = data.get('nuevo_costo')
                    if nuevo_costo is not None and nuevo_costo != materia.costo:
                        materia.costo = nuevo_costo
                        materia.save()
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
                    costo_unitario=materia.costo,
                )
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compras_mp_list')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

class CompraEditView(LoginRequiredMixin, UpdateView):
    model = Adquisicion
    form_class = CompraEditForm
    template_name = 'adquisicion/compra_edit.html'
    success_url = reverse_lazy('compras_mp_list')

    def get_queryset(self):
        # Solo permitir editar compras que estén pendientes o parcialmente recibidas
        return super().get_queryset().filter(estado__in=['pendiente', 'recibido_parcial'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detalle_formset'] = DetalleFormSet(self.request.POST, instance=self.object)
        else:
            context['detalle_formset'] = DetalleFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context['detalle_formset']

        # Verificar si el formset es válido
        if not detalle_formset.is_valid():
            # Mostrar errores del formset
            for form_detalle in detalle_formset:
                for field, errors in form_detalle.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Detalle - {field}: {error}")
            messages.error(self.request, "Corrige los errores en los detalles de materias primas.")
            return self.form_invalid(form)

        # Guardar la compra (el form ya incluye la factura)
        else:
            self.object = form.save()
            detalle_formset.instance = self.object
            detalles_guardados=detalle_formset.save()

            # Actualizar el costo de cada materia prima según el costo_unitario del detalle
            for detalle in detalles_guardados:
                # Verificar si el detalle tiene costo_unitario y es diferente al costo actual de la materia prima
                if detalle.costo_unitario and detalle.materia_prima:
                    materia_prima = detalle.materia_prima
                    # Comparar con tolerancia para decimales
                    if abs(materia_prima.costo - float(detalle.costo_unitario)) > 0.01:
                        materia_prima.costo = float(detalle.costo_unitario)
                        materia_prima.save()
                        messages.info(
                            self.request, 
                            f'Costo de "{materia_prima.nombre}" actualizado de ${materia_prima.costo} a ${detalle.costo_unitario}'
                        )
            messages.success(self.request, 'Compra actualizada exitosamente.')
            return redirect(self.success_url)

    def form_invalid(self, form):
        # Mostrar errores del formulario principal
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class MateriaPrimaDetalleView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            materia = MateriaPrima.objects.get(pk=pk)
            return JsonResponse({
                'id': materia.codigo,
                'nombre': materia.nombre,
                'concentracion': materia.concentracion or '',
                'conformacion': materia.conformacion or '',
                'tipo': materia.tipo_materia_prima or '',
                'medida': materia.unidad_medida or '',
                'costo':materia.costo or '',
            })
        except MateriaPrima.DoesNotExist:
            return JsonResponse({'error': 'Materia prima no encontrada'}, status=404)

@login_required
def list_mp_adquisiciones(request, template_name="adquisicion/mp_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

@login_required
def list_detalles_mp_adquisicion(request, id, template_name="adquisicion/detalles_mp_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicion.objects.filter(adquisicion=id)
        context = {
            'adquisicion': adquisicion,
            'detalles': detalles,
        }
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, context)

# Para los envases y embalajes 
class CompraEnvaseWizard(LoginRequiredMixin, SessionWizardView):
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
                factura=compra_data['factura'],
                tipo_adquisicion='env', 
                almacen = compra_data['almacen']
            )
            
            # Procesar 
            envase_forms = [f for f in form_list if isinstance(f, EnvasesForm)]
            for form in envase_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == EnvasesForm.EXISTING:
                    envase = data['envase_existente']

                    # Actualizar costo si se proporcionó uno nuevo
                    nuevo_costo = data.get('nuevo_costo')
                    if nuevo_costo is not None and nuevo_costo != envase.costo:
                        envase.costo = nuevo_costo
                        envase.save()
                else:
                    envase = EnvaseEmbalaje.objects.create(
                        tipo_envase_embalaje=data['tipo_envase_embalaje'],
                        formato=data['formato'],
                        costo=data['costo'],
                        codigo_envase=data['codigo_envase'],
                    )
                
                DetallesAdquisicionEnvase.objects.create(
                    adquisicion=compra,
                    envase_embalaje=envase,
                    cantidad=data['cantidad'],
                    costo_unitario=envase.costo
                )
            
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compras_env_list')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

class CompraEnvaseEditView(LoginRequiredMixin, UpdateView):
    model = Adquisicion
    form_class = CompraEditForm
    template_name = 'adquisicion/compra_envases_edit.html'
    success_url = reverse_lazy('compras_env_list')

    def get_queryset(self):
        # Solo compras editables
        return super().get_queryset().filter(estado__in=['pendiente', 'recibido_parcial'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['envase_formset'] = DetalleEnvaseFormSet(self.request.POST, instance=self.object)
            # Agrega aquí otros formsets si los tienes
        else:
            context['envase_formset'] = DetalleEnvaseFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        envase_formset = context['envase_formset']

        if envase_formset.is_valid():
            self.object = form.save()
            envase_formset.instance = self.object
            detalles_env_guardados=envase_formset.save()

            for det_env in detalles_env_guardados:
                if det_env.costo_unitario and det_env.envase_embalaje:
                    envase_embalaje=det_env.envase_embalaje
                    if abs(envase_embalaje.costo - float(det_env.costo_unitario)) > 0.01:
                        envase_embalaje.costo = float(det_env.costo_unitario)
                        envase_embalaje.save()
                        messages.info(
                            self.request, 
                            f'Costo de "{envase_embalaje.nombre}" actualizado de ${envase_embalaje.costo} a ${det_env.costo_unitario}'
                        )
            messages.success(self.request, 'Compra actualizada exitosamente.')
            return redirect(self.success_url)
        else:
            # Mostrar errores del formset
            for formset_errors in envase_formset.errors:
                for field, errors in formset_errors.items():
                    for error in errors:
                        messages.error(self.request, f"Envases - {field}: {error}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class EnvaseDetalleView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            envase = EnvaseEmbalaje.objects.get(pk=pk)
            if envase.formato:
                format = str(envase.formato.capacidad) + ' ' + envase.formato.unidad_medida
            else:
                format = ''
            return JsonResponse({
                'codigo': envase.codigo_envase,
                'formato': format,
                'tipo': envase.tipo_envase_embalaje.nombre or '',
                'costo': envase.costo or '',
            })
        except EnvaseEmbalaje.DoesNotExist:
            return JsonResponse({'error': 'Envase no encontrado'}, status=404)

@login_required
def list_env_adquisiciones(request, template_name="adquisicion/env_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles_envases')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

@login_required
def list_detalles_env_adquisicion(request, id, template_name="adquisicion/detalles_env_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicionEnvase.objects.filter(adquisicion=id)
        #.order_by('almacen')
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, locals())

# Para los insumos
class CompraInsumoWizard(LoginRequiredMixin, SessionWizardView):
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
                factura=compra_data['factura'],
                tipo_adquisicion='ins',
                almacen = compra_data['almacen']
            )
            
            # Procesar insumos
            insumo_forms = [f for f in form_list if isinstance(f, InsumosForm)]
            for form in insumo_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == InsumosForm.EXISTING:
                    insumo = data['insumo_existente']

                    # Actualizar costo si se proporcionó uno nuevo
                    nuevo_costo = data.get('nuevo_costo')
                    if nuevo_costo is not None and nuevo_costo != insumo.costo:
                        insumo.costo = nuevo_costo
                        insumo.save()
                else:
                    insumo = InsumosOtros.objects.create(
                        codigo=data['codigo'],
                        nombre=data['nombre'],
                        descripcion=data['descripcion'],
                        costo=data['costo'],
                    )
                
                DetallesAdquisicionInsumo.objects.create(
                    adquisicion=compra,
                    insumo=insumo,
                    cantidad=data['cantidad'],
                    costo_unitario=insumo.costo
                )
            
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compras_ins_list')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

class CompraInsumoEditView(LoginRequiredMixin, UpdateView):
    model = Adquisicion
    form_class = CompraEditForm
    template_name = 'adquisicion/compra_insumo_edit.html'
    success_url = reverse_lazy('compras_ins_list')

    def get_queryset(self):
        # Solo permitir editar compras que estén pendientes o parcialmente recibidas
        return super().get_queryset().filter(estado__in=['pendiente', 'recibido_parcial'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['insumo_formset'] = DetalleInsumoFormSet(self.request.POST, instance=self.object)
        else:
            context['insumo_formset'] = DetalleInsumoFormSet(instance=self.object)

            # Depuración: Verificar que los costos se están cargando
        for form in context['insumo_formset']:
            if form.instance.id and form.instance.costo_unitario:
                print(f"Insumo: {form.instance.insumo.nombre}, Costo: {form.instance.costo_unitario}")
            elif form.instance.id and form.instance.insumo:
                print(f"Insumo: {form.instance.insumo.nombre}, Costo inicial: {form.instance.insumo.costo}")
                
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context['insumo_formset']

        # Verificar si el formset es válido
        if not detalle_formset.is_valid():
            # Mostrar errores del formset
            for form_detalle in detalle_formset:
                for field, errors in form_detalle.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Detalle - {field}: {error}")
            messages.error(self.request, "Corrige los errores en los detalles de insumos.")
            return self.form_invalid(form)

        # Guardar la compra (el form ya incluye la factura)
        else:
            self.object = form.save()
            detalle_formset.instance = self.object
            det_ins_guardados=detalle_formset.save()

            for det_ins in det_ins_guardados:
                if det_ins.costo_unitario and det_ins.insumo:
                    insumo = det_ins.insumo

                    if abs(insumo.costo - float(det_ins.costo_unitario)) > 0.01:
                        insumo.costo = float(det_ins.costo_unitario)
                        insumo.save()
                        messages.info(
                            self.request, 
                            f'Costo de "{insumo.nombre}" actualizado de ${insumo.costo} a ${det_ins.costo_unitario}'
                        )
            messages.success(self.request, 'Compra actualizada exitosamente.')
            return redirect(self.success_url)

    def form_invalid(self, form):
        # Mostrar errores del formulario principal
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class InsumoDetalleView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            insumo = InsumosOtros.objects.get(pk=pk)
            return JsonResponse({
                'codigo': insumo.codigo,
                'nombre': insumo.nombre or '',
                'descripcion': insumo.descripcion or '',
                'costo': insumo.costo or '',
            })
        except InsumosOtros.DoesNotExist:
            return JsonResponse({'error': 'Insumo no encontrado'}, status=404)

@login_required
def list_ins_adquisiciones(request, template_name="adquisicion/ins_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles_insumos')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

@login_required
def list_detalles_ins_adquisicion(request, id, template_name="adquisicion/detalles_ins_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicionInsumo.objects.filter(adquisicion=id)
        #.order_by('almacen')
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, locals())

# Para los productos
class CompraProductoWizard(LoginRequiredMixin, SessionWizardView):
    file_storage = file_storage
    # Diccionario que mapea cada paso con su template
    template_dict = {
        'compra': 'adquisicion/compra_form.html',
        'cantidad': 'adquisicion/cantidad_form.html',
        'producto': 'adquisicion/producto_form.html',  # Para todos los pasos producto_*
    }

    def get_template_names(self):
        """Determina qué plantilla usar para el paso actual"""
        current_step = self.steps.current
        
        # Si es un paso de producto, usa el template genérico
        if current_step.startswith('producto_'):
            return [self.template_dict['producto']]
        
        # Para pasos conocidos, usa su template específico
        if current_step in self.template_dict:
            return [self.template_dict[current_step]]
        
        # Fallback por defecto
        return ['adquisicion/wizard_base.html']

    form_list = [
        ('compra', CompraForm),
        ('cantidad', CantidadProductosForm),
    ]

    def get_form_list(self):
        """Versión robusta que siempre retorna al menos los formularios base"""
        form_list = OrderedDict(self.form_list)
        
        # Agregar pasos dinámicos si hay datos de cantidad
        try:
            cantidad_data = self.storage.get_step_data('cantidad')
            if cantidad_data and 'cantidad-cantidad' in cantidad_data:
                num_productos = int(cantidad_data['cantidad-cantidad'][0])
                for i in range(num_productos):
                    form_list[f'producto_{i}'] = ProductosForm
        except (KeyError, ValueError, TypeError):
            pass
        return form_list
    
    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        # Para los pasos de producto, intentar mantener la selección previa
        if step.startswith('producto_'):
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
                ('cantidad', CantidadProductosForm),
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
                ('cantidad', CantidadProductosForm),
            ])

        # Añadir información específica del paso
        current_step = self.steps.current
        if current_step.startswith('producto_'):
            producto_num = int(current_step.split('_')[1]) + 1
            context['step_title'] = f"Producto {producto_num}"
        else:
            context['step_title'] = {
                'compra': 'Información General',
                'cantidad': 'Cantidad de Productos'
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
            'cantidad': "Cantidad de productos",
        }
        
        if self.steps.current.startswith('producto_'):
            try:
                index = int(self.steps.current.split('_')[1]) + 1
                return f"Producto {index}"
            except (ValueError, IndexError):
                return "Registro de productos"
        
        return titles.get(self.steps.current, "Paso del Proceso")
    
    def done(self, form_list, **kwargs):
        # Procesamiento seguro de los datos
        try:
            compra_data = [f for f in form_list if isinstance(f, CompraForm)][0].cleaned_data
            cantidad_data = [f for f in form_list if isinstance(f, CantidadProductosForm)][0].cleaned_data
            
            # Crear compra
            compra = Adquisicion.objects.create(
                fecha_compra=compra_data['fecha_compra'],
                importada=compra_data['importada'],
                factura=compra_data['factura'],
                tipo_adquisicion='prod',
                almacen = compra_data['almacen']
            )
            
            # Procesar productos
            producto_forms = [f for f in form_list if isinstance(f, ProductosForm)]
            for form in producto_forms[:cantidad_data['cantidad']]:
                data = form.cleaned_data
                
                if data['opcion'] == ProductosForm.EXISTING:
                    producto = data['producto_existente']
                    
                    # Actualizar costo si se proporcionó uno nuevo 
                    nuevo_costo = data.get('nuevo_costo')
                    if nuevo_costo is not None and nuevo_costo != producto.costo:
                        producto.costo = nuevo_costo
                        producto.save()
                else:
                    producto = Producto.objects.create(
                        codigo_producto=data['codigo_producto'],
                        nombre_comercial=data['nombre_comercial'],                        
                        costo=data['costo']
                    )                
                DetallesAdquisicionProducto.objects.create(
                    adquisicion=compra,
                    producto=producto,
                    cantidad=data['cantidad'],
                    costo_unitario=producto.costo
                )
            
            # Limpiar almacenamiento
            self.storage.reset()
            return redirect('compras_prod_list')
        
        except Exception as e:
            print(f"Error al procesar compra: {e}")
            # Manejar el error adecuadamente
            return redirect('error_page')

class CompraProductoEditView(LoginRequiredMixin, UpdateView):
    model = Adquisicion
    form_class = CompraEditForm
    template_name = 'adquisicion/compra_producto_edit.html'
    success_url = reverse_lazy('compras_prod_list')

    def get_queryset(self):
        # Solo permitir editar compras que estén pendientes o parcialmente recibidas
        return super().get_queryset().filter(estado__in=['pendiente', 'recibido_parcial'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['producto_formset'] = DetalleProductoFormSet(self.request.POST, instance=self.object)
        else:
            context['producto_formset'] = DetalleProductoFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        detalle_formset = context['producto_formset']

        # Verificar si el formset es válido
        if not detalle_formset.is_valid():
            # Mostrar errores del formset
            for form_detalle in detalle_formset:
                for field, errors in form_detalle.errors.items():
                    for error in errors:
                        messages.error(self.request, f"Detalle - {field}: {error}")
            messages.error(self.request, "Corrige los errores en los detalles de productos.")
            return self.form_invalid(form)

        # Guardar la compra (el form ya incluye la factura)
        else:
            self.object = form.save()
            detalle_formset.instance = self.object
            det_prod_guardado = detalle_formset.save()

            for det_prod in det_prod_guardado:
                if det_prod.costo_unitario and det_prod.producto:
                    producto = det_prod.producto

                    if abs(producto.costo - decimal.Decimal(det_prod.costo_unitario)) > 0.01:
                        producto.costo = decimal.Decimal(det_prod.costo_unitario)
                        producto.save()
                        messages.info(
                            self.request, 
                            f'Costo de "{producto.nombre_comercial}" actualizado de ${producto.costo} a ${det_prod.costo_unitario}'
                        )
                        
            messages.success(self.request, 'Compra actualizada exitosamente.')
            return redirect(self.success_url)

    def form_invalid(self, form):
        # Mostrar errores del formulario principal
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class ProductoDetalleView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            producto = Producto.objects.get(pk=pk)
            # format = str(producto.formato.capacidad) + ' ' + producto.formato.unidad_medida
            return JsonResponse({
                'codigo_producto': producto.codigo_producto,
                'nombre_comercial': producto.nombre_comercial or '',
                # 'formato': format or '',
                'costo': producto.costo or '',
            })
        except Producto.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@login_required
def list_prod_adquisiciones(request, template_name="adquisicion/prod_list.html"):
    adquisiciones = Adquisicion.objects.annotate(
        num_ad=Count('detalles_productos')
    ).filter(num_ad__gt=0)
    return render(request, template_name, locals())

@login_required
def list_detalles_prod_adquisicion(request, id, template_name="adquisicion/detalles_prod_list.html"):
    adquisicion = get_object_or_404(Adquisicion, id=id)
    if adquisicion:
        detalles = DetallesAdquisicionProducto.objects.filter(adquisicion=id)
        #.order_by('almacen')
    else:
        messages.error(request, "Error al acceder a esa adquisición")
    return render(request, template_name, locals())

@login_required
def compra_exitosa(request):
    return render(request, 'adquisicion/exito.html')

class CompraEditWizard(LoginRequiredMixin, SessionWizardView):
    """Wizard para editar una compra existente"""
    file_storage = file_storage
    
    template_dict = {
        'compra': 'adquisicion/compra_form.html',
        'cantidad': 'adquisicion/cantidad_form.html',
        'materia': 'adquisicion/materia_form.html',
    }
    form_list = [
        ('compra', CompraForm),
        ('cantidad', CantidadMateriasForm),
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.compra = None
    
    def dispatch(self, request, *args, **kwargs):
        self.compra = get_object_or_404(Adquisicion, pk=kwargs['pk'])
        
        # Verificar permisos
        if not self.compra.puede_editarse():
            messages.error(request, 'Esta compra no puede ser editada porque ya está completada o cancelada.')
            return redirect('compras_mp_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        
        if step == 'compra':
            initial.update({
                'fecha_compra': self.compra.fecha_compra,
                'importada': self.compra.importada,
                'almacen': self.compra.almacen,
                'observaciones': self.compra.observaciones,
            })
        elif step == 'cantidad':
            # Para edición, mostrar la cantidad actual de materias
            initial['cantidad'] = self.compra.detalles_adquisicion.count()
        
        return initial
    
    def get_form_list(self):
        """Genera los pasos dinámicos basados en la compra existente"""
        form_list = OrderedDict([
            ('compra', CompraForm),
            ('cantidad', CantidadMateriasForm),
        ])
        
        # Para edición, siempre usar la cantidad actual
        cantidad_detalles = self.compra.detalles_adquisicion.count()
        for i in range(cantidad_detalles):
            form_list[f'materia_{i}'] = MateriaPrimaForm
        
        return form_list
    
    def get_form(self, step=None, data=None, files=None):
        """Inyectar la instancia de materia prima en los formularios de edición"""
        form = super().get_form(step, data, files)
        
        if step and step.startswith('materia_') and hasattr(self, 'compra'):
            index = int(step.split('_')[1])
            detalles = list(self.compra.detalles_adquisicion.all())
            if index < len(detalles):
                detalle = detalles[index]
                form.instance = detalle.materia_prima
                form.detalle = detalle
                
                # Pre-cargar datos existentes
                form.initial.update({
                    'cantidad': detalle.cantidad,
                    'cantidad_recibida': detalle.cantidad_recibida,
                    'costo': detalle.costo_unitario or detalle.materia_prima.costo,
                })
        
        return form
    
    def done(self, form_list, **kwargs):
        """Guardar los cambios en la compra existente"""
        try:
            # Actualizar datos de compra
            compra_form = [f for f in form_list if isinstance(f, CompraForm)][0]
            for key, value in compra_form.cleaned_data.items():
                if key != 'observaciones':  # Manejar observaciones por separado
                    setattr(self.compra, key, value)
            
            self.compra.observaciones = compra_form.cleaned_data.get('observaciones', '')
            self.compra.save()
            
            # Actualizar o crear detalles
            materia_forms = [f for f in form_list if isinstance(f, MateriaPrimaForm)]
            
            # Actualizar detalles existentes
            existing_detalles = list(self.compra.detalles_adquisicion.all())
            
            for i, form in enumerate(materia_forms):
                data = form.cleaned_data
                
                if i < len(existing_detalles):
                    # Actualizar detalle existente
                    detalle = existing_detalles[i]
                    detalle.cantidad = data['cantidad']
                    
                    # Solo actualizar costo si se proporcionó
                    if data.get('costo'):
                        detalle.costo_unitario = data['costo']
                    
                    detalle.save()
                else:
                    # Crear nuevo detalle (si se aumentó la cantidad)
                    # Similar a la creación original
                    pass
            
            # Actualizar estado basado en recepciones
            self.actualizar_estado_compra()
            
            self.storage.reset()
            messages.success(self.request, 'Compra actualizada exitosamente.')
            return redirect('compras_mp_list')
            
        except Exception as e:
            messages.error(self.request, f'Error al actualizar: {str(e)}')
            return redirect('compras_mp_list')
    
    def actualizar_estado_compra(self):
        """Actualiza el estado de la compra basado en las cantidades recibidas"""
        total_pendiente = sum(d.cantidad_pendiente for d in self.compra.detalles_adquisicion.all())
        
        if total_pendiente <= 0:
            self.compra.estado = 'completado'
        else:
            # Verificar si ya se recibió algo
            total_recibido = sum(d.cantidad_recibida or 0 for d in self.compra.detalles_adquisicion.all())
            if total_recibido > 0:
                self.compra.estado = 'recibido_parcial'
            else:
                self.compra.estado = 'pendiente'
        
        self.compra.save()

class RecepcionParcialView(LoginRequiredMixin, View):
    """Vista para registrar recepción parcial de mercancía"""
    
    def get(self, request, pk):
        compra = get_object_or_404(Adquisicion, pk=pk)
        
        if compra.estado == 'completado':
            messages.warning(request, 'Esta compra ya ha sido completada.')
            return redirect('compras_mp_list')
        
        return render(request, 'adquisicion/recepcion_parcial.html', {
            'compra': compra,
            'detalles': compra.detalles_adquisicion.all(),
        })
    
    def post(self, request, pk):
        compra = get_object_or_404(Adquisicion, pk=pk)
        
        # Procesar cantidades recibidas
        for detalle in compra.detalles_adquisicion.all():
            cantidad_recibida_key = f'cantidad_recibida_{detalle.id}'
            if cantidad_recibida_key in request.POST:
                nueva_cantidad = request.POST[cantidad_recibida_key]
                if nueva_cantidad:
                    detalle.cantidad_recibida = float(nueva_cantidad)
                    detalle.save()
        
        # Actualizar estado
        compra.estado = 'recibido_parcial'
        compra.save()
        
        messages.success(request, 'Recepción registrada exitosamente.')
        return redirect('compras_mp_list')