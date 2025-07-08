from django.core.files.storage.filesystem import FileSystemStorage
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.forms import formset_factory
#nuevo wizard
from formtools.wizard.views import SessionWizardView
#------------------------------------------
#from InsumosOtros.models import InsumosOtros
from envase_embalaje.models import EnvaseEmbalaje
from materia_prima.models import MateriaPrima
from .models import Adquisicion, MateriaPrimaAdquisicion #, EnvaseAdquisicion, InsumosAdquisicion
from .forms import PasoAdquisicionForm, PasoMateriaPrimaForm #MateriaPrimaAdquisicionForm, EnvaseAdquisicionForm, InsumosAdquisicionForm,  \

# Vistas para MateriaPrimaAdquisicion
class MateriaPrimaAdquisicionListView(ListView):
    model = MateriaPrimaAdquisicion
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_list.html'
    context_object_name = 'adquisiciones'

class MateriaPrimaAdquisicionDetailView(DetailView):
    model = MateriaPrimaAdquisicion
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_detail.html'
    context_object_name = 'adquisicion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

def materiaAdquisicionCreateView(request):
    envaseList = EnvaseEmbalaje.objects.all()
    materiaPrimaList = MateriaPrima.objects.all
    insumosList = InsumosOtros.objects.all()
    context = {
        'envaseList': envaseList,
        'materiaPrimaList': materiaPrimaList,
        'insumosList': insumosList
    }
    return render(request, 'adquisicion/materia_prima/materia_prima_adquisicion_form_add.html', context)

def materia_add(request):
    if request.method == 'POST':
        fechaCompra = request.POST.get('fecha')
        importada = True if request.POST.get('importada') else False
        factura = request.FILES.get('factura')
        # Captura las listas del formulario
        cantidadClonList = request.POST.getlist('cantidadClon')
        materiaClonList = request.POST.getlist('materiaClon')

        # Filtra materiaClonList para eliminar elementos vacíos
        materiaClonList = [materia for materia in materiaClonList if materia]

        # Filtra cantidadClonList para eliminar elementos que sean '0' o vacíos
        cantidadClonList = [cantidad for cantidad in cantidadClonList if cantidad and int(cantidad) > 0]

        try:
            with transaction.atomic():
                for i in range(len(materiaClonList)):
                    materia_obj = MateriaPrima.objects.filter(nombre=materiaClonList[i]).first()
                    materiaAdquisicion = MateriaPrimaAdquisicion.objects.filter(materia_prima=materia_obj)

                    if materiaAdquisicion.exists():
                        materiaAdquisicionExists = materiaAdquisicion.first()
                        materiaAdquisicionExists.fecha_compra = fechaCompra
                        materiaAdquisicionExists.factura = factura
                        materiaAdquisicionExists.importada = importada
                        materiaAdquisicionExists.cantidad += int(cantidadClonList[i])
                        materiaAdquisicionExists.save()
                    else:
                        adquisicion = MateriaPrimaAdquisicion(
                            fecha_compra=fechaCompra,
                            factura=factura,
                            importada=importada,
                            materia_prima=materia_obj,
                            cantidad=int(cantidadClonList[i])
                        )
                        adquisicion.save()

            # Si todo fue exitoso
            return JsonResponse({'success': True, 'message': 'Los datos se han guardado correctamente.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ocurrió un error durante la importación: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

class MateriaPrimaAdquisicionUpdateView(UpdateView):
    model = MateriaPrimaAdquisicion
    form_class = PasoMateriaPrimaForm #MateriaPrimaAdquisicionForm
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_form_edit.html'
    success_url = reverse_lazy('materia_prima_adquisicion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de materia prima actualizada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)

# Vistas para EnvaseAdquisicion
""" class EnvaseAdquisicionListView(ListView):
    model = EnvaseAdquisicion
    template_name = 'adquisicion/envase/envase_adquisicion_list.html'
    context_object_name = 'adquisiciones'

class EnvaseAdquisicionDetailView(DetailView):
    model = EnvaseAdquisicion
    template_name = 'adquisicion/envase/envase_adquisicion_detail.html'
    context_object_name = 'adquisicion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

def envases_add(request):
    if request.method == 'POST':
        fechaCompra = request.POST.get('fecha')
        importada = True if request.POST.get('importada') else False
        factura = request.FILES.get('factura')

        # Captura las listas del formulario
        cantidadClonList = request.POST.getlist('cantidadClon')
        envaseClonList = request.POST.getlist('envaseClon')

        # Filtra envaseClonList para eliminar elementos vacíos
        envaseClonList = [envase for envase in envaseClonList if envase]

        # Filtra cantidadClonList para eliminar elementos que sean '0' o vacíos
        cantidadClonList = [cantidad for cantidad in cantidadClonList if cantidad and int(cantidad) > 0]

        try:
            with transaction.atomic():
                for i in range(len(envaseClonList)):
                    envase_obj = EnvaseEmbalaje.objects.filter(codigo_envase=envaseClonList[i]).first()
                    envaseAdquisicion = EnvaseAdquisicion.objects.filter(envase=envase_obj)

                    if envaseAdquisicion.exists():
                        envaseAdquisicionExists = envaseAdquisicion.first()
                        envaseAdquisicionExists.fecha_compra = fechaCompra
                        envaseAdquisicionExists.factura = factura
                        envaseAdquisicionExists.importada = importada
                        envaseAdquisicionExists.cantidad += int(cantidadClonList[i])
                        envaseAdquisicionExists.save()
                    else:
                        adquisicion = EnvaseAdquisicion(
                            fecha_compra=fechaCompra,
                            factura=factura,
                            importada=importada,
                            envase=envase_obj,
                            cantidad=int(cantidadClonList[i])
                        )
                        adquisicion.save()

            # Si todo fue exitoso
            return JsonResponse({'success': True, 'message': 'Los datos se han guardado correctamente.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ocurrió un error durante la importación: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

def envaseAdquisicionCreateView(request):
    envaseList = EnvaseEmbalaje.objects.all()
    materiaPrimaList = MateriaPrima.objects.all
    insumosList = InsumosOtros.objects.all()
    context = {
        'envaseList': envaseList,
        'materiaPrimaList': materiaPrimaList,
        'insumosList': insumosList
    }
    return render(request, 'adquisicion/envase/envase_adquisicion_form.html', context)

class EnvaseAdquisicionUpdateView(UpdateView):
    model = EnvaseAdquisicion
    form_class = EnvaseAdquisicionForm
    template_name = 'adquisicion/envase/envase_adquisicion_form_edit.html'
    success_url = reverse_lazy('envase_adquisicion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de envase actualizada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)

# Vistas para InsumosAdquisicion
class InsumosAdquisicionListView(ListView):
    model = InsumosAdquisicion
    template_name = 'adquisicion/insumos/insumos_adquisicion_list.html'
    context_object_name = 'adquisiciones'

class InsumosAdquisicionDetailView(DetailView):
    model = InsumosAdquisicion
    template_name = 'adquisicion/insumos/insumos_adquisicion_detail.html'
    context_object_name = 'adquisicion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

def insumosAdquisicionCreateView(request):
    envaseList = EnvaseEmbalaje.objects.all()
    materiaPrimaList = MateriaPrima.objects.all
    insumosList = InsumosOtros.objects.all()
    context = {
        'envaseList': envaseList,
        'materiaPrimaList': materiaPrimaList,
        'insumosList': insumosList
    }
    return render(request, 'adquisicion/insumos/insumos_adquisicion_form.html', context)

def insumos_add(request):
    if request.method == 'POST':
        fechaCompra = request.POST.get('fecha')
        importada = True if request.POST.get('importada') else False
        factura = request.FILES.get('factura')

        # Captura las listas del formulario
        cantidadClonList = request.POST.getlist('cantidadClon')
        insumosClonList = request.POST.getlist('insumosClon')

        # Filtra insumosClonList para eliminar elementos vacíos
        insumosClonList = [envase for envase in insumosClonList if envase]

        # Filtra cantidadClonList para eliminar elementos que sean '0' o vacíos
        cantidadClonList = [cantidad for cantidad in cantidadClonList if cantidad and int(cantidad) > 0]

        try:
            with transaction.atomic():
                for i in range(len(insumosClonList)):
                    insumo_obj = InsumosOtros.objects.filter(nombre=insumosClonList[i]).first()
                    insumoAdquisicion = InsumosAdquisicion.objects.filter(insumo=insumo_obj)

                    if insumoAdquisicion.exists():
                        insumoAdquisicionExists = insumoAdquisicion.first()
                        insumoAdquisicionExists.fecha_compra = fechaCompra
                        insumoAdquisicionExists.factura = factura
                        insumoAdquisicionExists.importada = importada
                        insumoAdquisicionExists.cantidad += int(cantidadClonList[i])
                        insumoAdquisicionExists.save()
                    else:
                        adquisicion = InsumosAdquisicion(
                            fecha_compra=fechaCompra,
                            factura=factura,
                            importada=importada,
                            insumo=insumo_obj,
                            cantidad=int(cantidadClonList[i])
                        )
                        adquisicion.save()

            # Si todo fue exitoso
            return JsonResponse({'success': True, 'message': 'Los datos se han guardado correctamente.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Ocurrió un error durante la importación: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

class InsumosAdquisicionUpdateView(UpdateView):
    model = InsumosAdquisicion
    form_class = InsumosAdquisicionForm
    template_name = 'adquisicion/insumos/insumos_adquisicion_form_edit.html'
    success_url = reverse_lazy('insumos_adquisicion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de insumos actualizada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)
 """

""" class AdquisicionWizard(SessionWizardView):
    template_name = 'adquisicion/materia_prima/wizard/adquisicion_wizard.html'  # Replace with your template
    file_storage = FileSystemStorage()
    form_list = [PasoAdquisicionForm]

    def get_form_list(self):
        print("Estoy aca")
        Dynamically construct the form list.
        form_lista = self.form_list  # Step 1: Always the AdquisicionForm
        print("---")
        
        if self.get_cleaned_data_for_step('0'): 
            print("entro acá")
            # If step 0 has been completed
            adquisicion_data = self.get_cleaned_data_for_step('0')
            num_materias_primas = adquisicion_data.get('cantidad', 0)
            for _ in range(num_materias_primas):  # Create the MateriaPrimaForms
                form_lista.append(PasoMateriaPrimaForm)
        else:
            print("Fallo el self.cleaned")
            if 'wizard_prev_step' in self.request.POST:
                # Guarda los datos del paso actual aunque no sean válidos
                form = self.get_form(data=self.request.POST, files=self.request.FILES)
                self.storage.set_step_data(self.steps.current, self.process_step(form))
                self.storage.current_step = self.steps.prev
                return self.render(self.get_form())
            elif 'wizard_steps_next' in self.request.POST:
                print("Aqui es donde continua...")
            else:
                print("Tambien fallo el request_POST")
            print(self.request.POST)
        return form_lista

    def post(self, request, *args, **kwargs):
        if 'wizard_prev_step' in request.POST:
            # Guarda los datos del paso actual aunque no sean válidos
            form = self.get_form(data=request.POST, files=request.FILES)
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            self.storage.current_step = self.steps.prev
            return self.render(self.get_form())
        return super().post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        Process all forms when done.
        adquisicion_data = form_list[0].cleaned_data
        materias_primas_data = [form.cleaned_data for form in form_list[1:]]

        from .models import Adquisicion, MateriaPrima  # Replace with your models
        adquisicion = Adquisicion.objects.create(**adquisicion_data)

        for materia_prima_data in materias_primas_data:
            MateriaPrima.objects.create(adquisicion=adquisicion, **materia_prima_data)

        # Redirect to a success page or display a summary
        return redirect('success_page')  # Replace with your success URL name 
        
def success_view(request):
        return render(request, 'adquisicion/success.html')
 """

def crear_adquisicion(request):
    DetalleFormSet = formset_factory(PasoMateriaPrimaForm, extra=1)
    
    if request.method == 'POST':
        form = PasoAdquisicionForm(request.POST)
        formset = DetalleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            adquisicion = form.save()
            
            total = 0
            for detalle_form in formset:
                if detalle_form.cleaned_data:
                    detalle = detalle_form.save(commit=False)
                    detalle.adquisicion = adquisicion
                    detalle.save()
                    total += detalle.subtotal
                    
                    # Actualizar inventario
                    """ inventario, created = Inventario.objects.get_or_create(
                        materia_prima=detalle.materia_prima
                    )
                    inventario.cantidad_disponible += detalle.cantidad
                    inventario.save() """
            
            adquisicion.total = total
            adquisicion.save()
            
            return redirect('lista_adquisiciones')
    else:
        form = PasoAdquisicionForm()
        formset = DetalleFormSet()
    
    return render(request, 'adquisicion/materia_prima/wizard/adquisicion_formset.html', {
        'form': form,
        'formset': formset,
    })

FORMS = [
    ("adquisicion", PasoAdquisicionForm),
    ("materia_prima", PasoMateriaPrimaForm),
]

TEMPLATES = {
    "adquisicion": "adquisicion/materia_prima/wizard/adquisicion_wizard.html",
    "materia_prima": "adquisicion/materia_prima/materia_prima_adquisicion_form.html",
}

class AdquisicionWizard(SessionWizardView):
    file_storage = FileSystemStorage()
    
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        # Procesar todos los formularios
        adquisicion_data = form_list[0].cleaned_data
        materias_data = form_list[1].cleaned_data
        
        # Crear adquisición
        adquisicion = Adquisicion.objects.create(
            factura=adquisicion_data['factura'],
            fecha=adquisicion_data['fecha'],
            cantidad_materias=adquisicion_data['cantidad_materias']
        )

        print("###---Adq---#")
        print(adquisicion.cantidad_materias)
        
        # Crear detalles y actualizar inventario
        for materia_data in materias_data:
            print("#---Entre a MP---#")
            detalle = MateriaPrimaAdquisicion.objects.create(
                adquisicion=adquisicion,
                materia_prima=materia_data['materia_prima'],
                cantidad=materia_data['cantidad'],
                #precio_unitario=materia_data['precio_unitario']
            )
            
            """ # Actualizar inventario
            inventario, created = Inventario.objects.get_or_create(
                materia_prima=detalle.materia_prima
            )
            inventario.cantidad_disponible += detalle.cantidad
            inventario.save() """
        
        return redirect('lista_adquisiciones')

def adquisicion_detalle(request, pk):
    adquisicion = get_object_or_404(MateriaPrimaAdquisicion, pk=pk)
    return render(request, 'adquisicion/materia_prima/wizard/adquisicion_detalle.html', {'adquisicion': adquisicion})


def wizard_adquisicion(request, step=1):
    # Si se accede por primera vez, inicializar la sesión
    if 'wizard_data' not in request.session:
        request.session['wizard_data'] = {
            'step1': None,
            'step2': None,
        }
    # Manejar el paso actual
    if step == 1:
        return paso1_adquisicion(request)
    elif step == 2:
        return paso2_materias(request)
    else:
        # Paso no válido, redirigir al paso 1
        return redirect('wizard_adquisicion_step', step=1)

def paso1_adquisicion(request):
    wizard_data = request.session['wizard_data']
    if request.method == 'POST':
        form = PasoAdquisicionForm(request.POST)
        if form.is_valid():
            # Guardar datos del paso 1
            wizard_data['step1'] = form.cleaned_data
            request.session['wizard_data'] = wizard_data
            request.session.modified = True
            return redirect('wizard_adquisicion_step', step=2)
    else:
        # Si hay datos guardados, mostrarlos
        if wizard_data['step1']:
            form = PasoAdquisicionForm(initial=wizard_data['step1'])
        else:
            form = PasoAdquisicionForm()
    return render(request, 'adquisicion/materia_prima/wizard/paso_1.html', {'form': form})

def paso2_materias(request):
    wizard_data = request.session['wizard_data']
    # Si no hay datos del paso 1, redirigir al paso 1
    if not wizard_data['step1']:
        return redirect('wizard_adquisicion_step', step=1)
    DetalleFormSet = formset_factory(PasoMateriaPrimaForm, extra=1)
    if request.method == 'POST':
        formset = DetalleFormSet(request.POST)
        if 'volver' in request.POST:
            # Volver al paso 1
            return redirect('wizard_adquisicion_step', step=1)
        if formset.is_valid():
            # Guardar datos del paso 2
            wizard_data['step2'] = formset.cleaned_data
            request.session['wizard_data'] = wizard_data
            request.session.modified = True
            # Guardar en base de datos
            adquisicion = Adquisicion.objects.create(
                factura=wizard_data['step1']['factura'],
                fecha=wizard_data['step1']['fecha_compra'],
                importa=wizard_data['step1']['importada'],
                cantidad_materias=wizard_data['step1']['cantidad']
            )
            for detalle_data in wizard_data['step2']:
                if detalle_data:  # Evitar diccionarios vacíos
                    detalle = MateriaPrima(
                        nombre=detalle_data['nombre'],
                        tipo=detalle_data['tipo_materia_prima'],
                        conformacion=detalle_data['conformacion'],
                        unidad_medida=detalle_data['unidad_medida'],
                        concentracion=detalle_data['concentracion'],
                        costo=detalle_data['costo'],
                        almacen=detalle_data['almacen'],
                        ficha_tecnica=detalle_data['ficha_tecnica'],
                        hoja_seguridad=detalle_data['hoja_seguridad']
                    )
                    detalle.save()
                    # Actualizar inventario
                    #---
            # Limpiar la sesión
            del request.session['wizard_data']
            return redirect('lista_adquisiciones')  # Redirigir a la lista
    else:
        # Si hay datos guardados del paso 2, cargarlos
        if wizard_data['step2']:
            formset = DetalleFormSet(initial=wizard_data['step2'])
        else:
            formset = DetalleFormSet()
    return render(request, 'adquisicion/materia_prima/paso_2.html', {'formset': formset})
