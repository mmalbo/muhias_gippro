from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from .models import *
from .forms import *
from produccion.choices import ESTADOS_ENV
from inventario.models import Inv_Producto, Producto, Inv_Envase, Inv_Insumos
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_Prod

# Create your views here.
@login_required
def lista_solicitudes_envasado(request):
    """Listado de todas las solicitudes"""
    solicitudes = SolicitudEnvasado.objects.all()
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
    
    return render(request, 'produccion/envasado/lista_solicitudes.html', {
        'solicitudes': solicitudes,
        'estados': ESTADOS_ENV
    })

class SolicitudEnvasadoCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudEnvasado
    form_class = SolicitudEnvasadoForm
    template_name = 'produccion/envasado/solicitud_form.html'
    success_url = reverse_lazy('envasado:lista_solicitudes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los envases disponibles (a través de Inv_Envase)
        envases_disponibles = []
        for inv_envase in Inv_Envase.objects.filter(cantidad__gt=0).select_related('envase', 'almacen'):
            if inv_envase.envase:  # Verificar que la relación existe
                envases_disponibles.append({
                    'id': inv_envase.id,
                    'nombre': inv_envase.envase.nombre,
                    'codigo': inv_envase.envase.codigo_envase,
                    'tipo': inv_envase.envase.tipo_envase_embalaje,
                    'cantidad': inv_envase.cantidad,
                    'almacen': inv_envase.almacen.nombre if inv_envase.almacen else 'N/A'
                })
        context['envases_disponibles'] = envases_disponibles
        
        # Obtener todos los insumos disponibles
        """inv_insumo = Inv_Insumos.objects.filter(
            cantidad__gt=0
        ).select_related('insumos', 'almacen').order_by('insumos__nombre')"""
        insumos_disponibles = []
        for inv_insumo in Inv_Insumos.objects.filter(cantidad__gt=0).select_related('insumos', 'almacen'):
            if inv_insumo.insumos:  # Verificar que la relación existe
                insumos_disponibles.append({
                    'id': inv_insumo.id,
                    'nombre': inv_insumo.insumos.nombre,
                    'cantidad': inv_insumo.cantidad,
                    #'unidad': inv_insumo.insumos.unidad_medida,
                    'almacen': inv_insumo.almacen.nombre if inv_insumo.almacen else 'N/A'
                })
        context['insumos_disponibles'] = insumos_disponibles

        # Debug
        print(f"Envases disponibles: {len(envases_disponibles)}")
        print(f"Insumos disponibles: {len(insumos_disponibles)}")

        return context

    def form_valid(self, form):
        messages.success(self.request, 'Solicitud de envasado creada exitosamente.')
        return super().form_valid(form)

    """def form_valid(self, form):
        try:
            with transaction.atomic():
               response = super().form_valid(form)

               # Crear vale de solicitud
               id_almacen = self.object.lote_produccion_origen.almacen
               print(id_almacen)
               almacen_obj = Almacen.objects.get(id=id_almacen)
               vale = Vale_Movimiento_Almacen.objects.create(
                   tipo = 'Solicitud a envasado',
                   entrada = False,
                   origen = almacen_obj.nombre,
                   destino = 'Planta'
                   lote_No = self.object.folio,
                   estado = 'confirmado'
               )
                
        messages.success(self.request, 'Solicitud de envasado creada exitosamente.')
        return """

    def form_invalid(self, form):
        # Imprimir errores en consola
        print("=== ERRORES DEL FORMULARIO ===")
        print(form.errors)
        print(form.non_field_errors())
    
        # Para ver también los errores específicos de cada campo
        for field, errors in form.errors.items():
            print(f"Campo {field}: {errors}")
    
        messages.error(self.request, f'Por favor corrige los errores en el formulario: {form.errors}')
        return super().form_invalid(form)

# API endpoints para AJAX
@login_required
def obtener_detalle_lote(request):
    """Obtener detalles de un lote especifico"""
    lote_id = request.GET.get('lote_id')
    if lote_id:
        try:
            lote = Inv_Producto.objects.select_related('producto', 'almacen').get(id=lote_id)
            return JsonResponse({
                'success': True,
                'producto': lote.producto.nombre_comercial,
                'cantidad_disponible': float(lote.cantidad),
                'almacen': lote.almacen.nombre if lote.almacen else 'N/A',
                'lote': lote.lote_produccion
            })
        except Inv_Producto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Lote no encontrado'})
    return JsonResponse({'success': False, 'error': 'ID de lote no proporcionado'})

@login_required
def obtener_detalle_envase(request):
    """Obtener detalles de un envase específico"""
    envase_id = request.GET.get('envase_id')
    if envase_id:
        try:
            envase = Inv_Envase.objects.select_related('envase', 'almacen').get(id=envase_id)
            return JsonResponse({
                'success': True,
                'nombre': envase.envase.nombre,
                'codigo': envase.envase.codigo_envase,
                'tipo': envase.envase.tipo_envase_embalaje,
                'cantidad_disponible': envase.cantidad,
                'almacen': envase.almacen.nombre if envase.almacen else 'N/A',
                'presentacion': envase.presentacion if hasattr(envase, 'presentacion') else ''
            })
        except Inv_Envase.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Envase no encontrado'})
    return JsonResponse({'success': False, 'error': 'ID de envase no proporcionado'})

@login_required
def obtener_detalle_insumo(request):
    """Obtener detalles de un insumo específico"""
    insumo_id = request.GET.get('insumo_id')
    if insumo_id:
        try:
            insumo = Inv_Insumos.objects.select_related('insumos', 'almacen').get(id=insumo_id)
            return JsonResponse({
                'success': True,
                'nombre': insumo.insumos.nombre,
                'cantidad_disponible': insumo.cantidad,
                'unidad': insumo.insumos.unidad_medida,
                'almacen': insumo.almacen.nombre if insumo.almacen else 'N/A'
            })
        except Inv_Insumos.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Insumo no encontrado'})
    return JsonResponse({'success': False, 'error': 'ID de insumo no proporcionado'})

@login_required
def detalle_solicitud_envasado(request, pk):
    """Ver detalle de una solicitud"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    # Verificar disponibilidad de producto a granel
    disponible = solicitud.lote_produccion_origen.cantidad >= solicitud.cantidad_solicitada
    
    return render(request, 'produccion/envasado/detalle_solicitud.html', {
        'solicitud': solicitud,
        'disponible': disponible
    })

@login_required
def iniciar_envasado(request, pk):
    """Iniciar el proceso de envasado"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    if solicitud.estado != 'Planificada':
        messages.error(request, 'Esta solicitud no está preparada para iniciar.')
        return redirect('envasado:detalle_solicitud_envasado', pk=pk)
    
    solicitud.estado = 'en_proceso'
    solicitud.fecha_inicio = timezone.now().date()
    solicitud.save()
    
    messages.success(request, 'Proceso de envasado iniciado.')
    return redirect('envasado:registrar_lote_envasado', pk=pk)

def concluir_envasado(request, pk):
    """Iniciar el proceso de envasado"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    if solicitud.estado != 'en_proceso':
        messages.error(request, 'Esta solicitud no está preparada para concluir.')
        return redirect('envasado:detalle_solicitud_envasado', pk=pk)
    
    solicitud.estado = 'completada'
    solicitud.fecha_fin = timezone.now().date()
    solicitud.save()
    
    messages.success(request, 'Proceso de envasado concluido.')
    return redirect('envasado:lista_solicitudes')

@login_required
def cancelar_solicitud(request, pk):
    """Cancelar una solicitud pendiente"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    # Verificar que el usuario sea el solicitante
    if solicitud.solicitante != request.user:
        messages.error(request, 'No tiene permiso para cancelar esta solicitud')
        return redirect('envasado:detalle_solicitud', pk=pk)
    
    # Verificar que esté pendiente
    if solicitud.estado != 'Planificada':
        messages.error(request, 'Solo se pueden cancelar solicitudes planificadas')
        return redirect('envasado:detalle_solicitud', pk=pk)
    
    with transaction.atomic():
        solicitud.estado = 'cancelada'
        solicitud.save()
        messages.success(request, 'Solicitud cancelada exitosamente')
    
    return redirect('envasado:lista_solicitudes')

@login_required
def registrar_lote_envasado(request, pk):
    """Registrar un lote de producto envasado"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    if request.method == 'POST':
        form = LoteEnvasadoForm(request.POST, solicitud=solicitud)
        if form.is_valid():
            with transaction.atomic():
                lote = form.save(commit=False)
                lote.solicitud = solicitud
                lote.responsable = request.user
                lote.save()
                
                # Registrar consumos de insumos
                for insumo_data in form.cleaned_data['consumos']:
                    ConsumoInsumoEnvasado.objects.create(
                        lote=lote,
                        **insumo_data
                    )
                
                # Verificar si ya se completó toda la cantidad solicitada
                """Definir el form para establecer el cierre del envasado y registrar la cantidad real"""
                
                messages.success(request, 'Lote registrado exitosamente.')
                return redirect('detalle_solicitud_envasado', pk=pk)
    else:
        form = LoteEnvasadoForm(solicitud=solicitud)
    
    return render(request, 'produccion/envasado/registrar_lote.html', {
        'form': form,
        'solicitud': solicitud
    })