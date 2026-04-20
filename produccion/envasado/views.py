from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse, reverse_lazy
import re
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

        return context

    def form_valid(self, form):
        messages.success(self.request, 'Solicitud de envasado creada exitosamente.')
        return super().form_valid(form)

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
def cancelar_solicitud(request, pk):
    """Cancelar una solicitud pendiente"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    # Verificar que el usuario sea el solicitante
    if solicitud.solicitante != request.user:
        messages.error(request, 'No tiene permiso para cancelar esta solicitud')
        return redirect('envasado:detalle_solicitud_envasado', pk=pk)
    
    # Verificar que esté pendiente
    if solicitud.estado != 'Planificada':
        messages.error(request, 'Solo se pueden cancelar solicitudes planificadas')
        return redirect('envasado:detalle_solicitud_envasado', pk=pk)
    
    with transaction.atomic():
        solicitud.estado = 'cancelada'
        solicitud.save()
        messages.success(request, 'Solicitud cancelada exitosamente')
    
    return redirect('envasado:lista_solicitudes')

@login_required
def iniciar_envasado(request, pk):
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)

    # Validación de estado
    if solicitud.estado != 'Planificada':
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'La solicitud no está planificada'})
        messages.error(request, 'Esta solicitud no está planificada para iniciar.')
        return redirect('envasado:detalle_solicitud_envasado', pk=pk)

    # Obtener detalles de envases
    detalles_envase = DetalleEnvasado.objects.filter(solicitud=solicitud)
    if not detalles_envase.exists():
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'No hay envases definidos en la solicitud'})
        messages.error(request, 'La solicitud no tiene envases asociados.')
        return redirect('envasado:detalle_solicitud_envasado', pk=pk)

    # Tomar el primer envase para determinar el formato (ajustable según necesidad)
    primer_envase = detalles_envase.first().presentacion.envase
    formato = primer_envase.formato  # Campo 'formato' en el modelo Envase (ej: "500ml")

    # Generar lote destino: lote_origen + "-" + formato
    """lote_origen_str = solicitud.lote_produccion_origen.lote  # campo 'lote' en Inv_Producto
    lote_destino_str = f"{lote_origen_str}-{formato}"""
    # Generar lote destino: reemplazar sufijo "-A granel" o "-granel" por el formato del envase
    lote_origen = solicitud.lote_produccion_origen.lote
    # Patrón para eliminar el sufijo (case insensitive, permite espacios opcionales)
    lote_base = re.sub(r'(-A\s*granel|-granel)$', '', lote_origen, flags=re.IGNORECASE)
    lote_destino_str = f"{lote_base}-{formato}"

    # GET: mostrar formulario con el lote destino generado
    if request.method == 'GET':
        return render(request, 'produccion/envasado/iniciar_envasado.html', {
            'solicitud': solicitud,
            'lote_destino': lote_destino_str,
        })

    # POST: procesar inicio del envasado
    try:
        data = json.loads(request.body)
        fecha_vencimiento = data.get('fecha_vencimiento')
        observaciones = data.get('observaciones_proceso', '')

        if not fecha_vencimiento:
            return JsonResponse({'success': False, 'error': 'La fecha de vencimiento es obligatoria'})

        with transaction.atomic():
            # 1. Obtener o crear el ProductoCatalogo con el formato correspondiente
            producto_granel = solicitud.lote_produccion_origen.producto            

            # 2. Obtener o crear el Inv_Producto (lote destino)
            inventario_destino, _ = Inv_Producto.objects.get_or_create(
                lote=lote_destino_str,
                producto=producto_granel,
                almacen=solicitud.lote_produccion_origen.almacen,
                defaults={'cantidad': 0}   # cantidad se actualizará al concluir
            )

            # 3. Actualizar la solicitud
            solicitud.estado = 'en_proceso'
            solicitud.fecha_inicio = timezone.now().date()
            solicitud.producto_destino = producto_granel
            solicitud.lote_destino = inventario_destino
            solicitud.fecha_vencimiento = fecha_vencimiento
            solicitud.observaciones = observaciones
            solicitud.save()

            return JsonResponse({
                'success': True,
                'message': f'Envasado iniciado. Lote destino: {lote_destino_str}',
                'redirect_url': reverse('envasado:detalle_solicitud_envasado', args=[solicitud.pk])
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

"""@login_required    
def concluir_envasado(request, pk):
    # Iniciar el proceso de envasado
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
def registrar_lote_envasado(request, pk):
    # Registrar un lote de producto envasado
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
                # Definir el form para establecer el cierre del envasado y registrar la cantidad real
                
                messages.success(request, 'Lote registrado exitosamente.')
                return redirect('detalle_solicitud_envasado', pk=pk)
    else:
        form = LoteEnvasadoForm(solicitud=solicitud)
    
    return render(request, 'produccion/envasado/registrar_lote.html', {
        'form': form,
        'solicitud': solicitud
    })"""

@csrf_exempt
@login_required
def concluir_envasado(request, pk):
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)

    # Solo se puede concluir si está en proceso
    if solicitud.estado != 'en_proceso':
        if request.method == 'POST':
            return JsonResponse({'success': False, 'error': 'La solicitud no está en proceso'})
        messages.error(request, 'Esta solicitud no está en proceso para concluir.')
        return redirect('envasado:detalle_solicitud', pk=pk)

    # GET: mostrar formulario con datos planificados
    if request.method == 'GET':
        # Obtener detalles de envases planificados
        detalles_envase = DetalleEnvasado.objects.filter(solicitud=solicitud)
        envases_planificados = []
        for det in detalles_envase:
            capacidad = det.presentacion.envase.formato.capacidad if hasattr(det.presentacion.envase.formato, 'capacidad') else 1
            envases_planificados.append({
                'id': det.id,
                'nombre': det.presentacion.envase.nombre,
                'capacidad': float(capacidad),
                'cantidad_solicitada': det.cantidad_unidades,
                'cantidad_real': det.cantidad_unidades,  # precargado igual
            })

        # Obtener consumos planificados
        consumos = solicitud.consumos.select_related('insumo__insumos').all()
        insumos_planificados = []
        for con in consumos:
            insumos_planificados.append({
                'id': con.id,
                'nombre': con.insumo.insumos.nombre,
                'cantidad_solicitada': float(con.cantidad_unidades),
                'cantidad_real': float(con.cantidad_unidades),
            })

        # Calcular total teórico (volumen) y pérdida estimada
        total_teorico = sum(e['capacidad'] * e['cantidad_solicitada'] for e in envases_planificados)
        print(total_teorico)
        granel_solicitado = float(solicitud.cantidad_solicitada)
        perdida_estimada = granel_solicitado - total_teorico
        print(perdida_estimada)

        context = {
            'solicitud': solicitud,
            'envases_planificados': envases_planificados,
            'insumos_planificados': insumos_planificados,
            'granel_solicitado': granel_solicitado,
            'total_teorico': total_teorico,
            'perdida_estimada': perdida_estimada,
        }
        return render(request, 'produccion/envasado/concluir_envasado.html', context)

    # POST: procesar datos reales
    try:
        data = json.loads(request.body)
        envases_reales = data.get('envases', [])
        insumos_reales = data.get('insumos', [])
        observaciones_finales = data.get('observaciones_finales', '')

        # Recalcular total producido en volumen (litros/kg) a partir de las cantidades reales por envase
        total_producido_volumen = 0.0
        total_unidades = 0
        detalles_envase_actualizados = []

        # Obtener detalles originales para mapear capacidades
        detalles_envase_cap = DetalleEnvasado.objects.filter(solicitud=solicitud)
        detalles_originales = {d.id: d for d in detalles_envase_cap}

        for env in envases_reales:
            detalle_id = env.get('id')
            detalle_original = detalles_originales.get(detalle_id)
            if not detalle_original:
                continue
            capacidad = float(detalle_original.presentacion.envase.capacidad or 1)
            cantidad_real = float(env.get('cantidad_real', 0))
            total_unidades += cantidad_real
            total_producido_volumen += cantidad_real * capacidad
            detalles_envase_actualizados.append({
                'detalle_id': detalle_id,
                'cantidad_producida': cantidad_real,
                'observaciones': env.get('observaciones', '')
            })

        cantidad_perdida = float(solicitud.cantidad_solicitada) - total_producido_volumen
        if cantidad_perdida < 0:
            cantidad_perdida = 0

        with transaction.atomic():
            # 1. Actualizar el lote destino (Inv_Producto) con la cantidad real de unidades
            lote_destino = solicitud.lote_destino
            if lote_destino:
                lote_destino.cantidad = total_unidades   # cantidad en unidades (envases)
                lote_destino.save()

            # 2. Actualizar la solicitud
            solicitud.estado = 'completada'
            solicitud.fecha_fin = timezone.now().date()
            solicitud.unidades_producidas = total_unidades
            solicitud.cantidad_perdida = cantidad_perdida
            solicitud.consumos_reales = {
                'envases': detalles_envase_actualizados,
                'insumos': insumos_reales,
                'observaciones_finales': observaciones_finales,
            }
            solicitud.save()

            # 3. (Opcional) Crear vale de entrada si usas el sistema de movimientos
            # from .services import ServicioEnvasadoVales
            # vale = ServicioEnvasadoVales.crear_vale_entrada_envasado(...)

            return JsonResponse({
                'success': True,
                'message': f'Envasado concluido. Unidades producidas: {total_unidades}, Pérdida: {cantidad_perdida:.2f} L/kg',
                'redirect_url': reverse('envasado:detalle_solicitud_envasado', args=[solicitud.pk])
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})