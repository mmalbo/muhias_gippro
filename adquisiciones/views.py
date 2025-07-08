from django.core.files.storage.filesystem import FileSystemStorage
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls.base import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from formtools.wizard.views import SessionWizardView
from InsumosOtros.models import InsumosOtros
from envase_embalaje.models import EnvaseEmbalaje
from materia_prima.models import MateriaPrima
from .models import MateriaPrimaAdquisicion
#, EnvaseAdquisicion, InsumosAdquisicion
from .forms import MateriaPrimaAdquisicionForm, PasoAdquisicionForm, PasoMateriaPrimaForm
#, EnvaseAdquisicionForm, InsumosAdquisicionForm, 


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
    form_class = MateriaPrimaAdquisicionForm
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
"""
class EnvaseAdquisicionListView(ListView):
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
#------------!!!!!----------------#
class MateriaPrimaAdquisicionWizard(SessionWizardView):
    form_list = [PasoAdquisicionForm, PasoMateriaPrimaForm]
    template_name = 'adquisicion/materia_prima/wizard/wizard_form.html'
    file_storage = FileSystemStorage()

    def get_form_initial(self, step):
        initial = super().get_form_initial(step) or {}
        if step == '1':
            # Obtiene datos del paso 0 solo si el formulario es válido
            form = self.get_form(step='0', data=self.storage.get_step_data('0'))
            if form.is_valid():
                initial.update(form.cleaned_data)
                print("---INITIAL---")
                print(self.storage.get_step_data('0'))
        return initial

    def post(self, request, *args, **kwargs):
        print("#---WIZARD---#---STEP---")
        print(request.POST)
        if 'wizard_prev_step' in request.POST:
            # Guarda los datos del paso actual aunque no sean válidos
            form = self.get_form(data=request.POST, files=request.FILES)
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            self.storage.current_step = self.steps.prev
            return self.render(self.get_form())
        return super().post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        #try:
            # Validación explícita de todos los formularios
            if not all(form.is_valid() for form in form_list):
                raise ValueError("Por favor corrige los errores en los formularios")

            # Acceso seguro a cleaned_data
            paso1_data = form_list[0].cleaned_data
            paso2_data = form_list[1].cleaned_data

            """ if not paso2_data.get('materia_prima'):
                raise ValueError("Debes seleccionar una materia prima") """

            adquisicion = MateriaPrimaAdquisicion.objects.create(
                fecha_compra=paso1_data['fecha_compra'],
                factura=paso1_data.get('factura'),
                importada=paso1_data.get('importada', False),
                cantidad=paso1_data.get('cantidad', 1),
                #materia_prima=paso2_data['materia_prima']
            )
            print(adquisicion)
            print("------------")
            materia_p = MateriaPrima.objects.create(
                nombre = paso2_data.get['nombre'],
                tipo = paso2_data.get('tipo_materia_prima'),
                conf = paso2_data.get('conformacion'),
                unid = paso2_data.get('unidad_medida')
                
            )
            print("Entre")
            print(materia_p)

            return redirect('materia_prima_adquisicion_list')

    """ except Exception as e:
            messages.error(self.request, f"Error: {str(e)}")
            print("Estoy saliendo aqui")
            return self.render(self.get_form()) """
def adquisicion_detalle(request, pk):
    adquisicion = get_object_or_404(MateriaPrimaAdquisicion, pk=pk)
    return render(request, 'adquisicion/materia_prima/wizard/adquisicion_detalle.html', {'adquisicion': adquisicion})
