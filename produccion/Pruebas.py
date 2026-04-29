# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid

class SolicitudEnvasado(models.Model):
    """Modelo para solicitudes de envasado"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    folio = models.CharField(max_length=20, unique=True, editable=False)
    
    # Producto a granel (Producto_catalogo con formato='agranel')
    producto_granel = models.ForeignKey('Producto_catalogo', on_delete=models.PROTECT, 
                                       related_name='solicitudes_envasado_origen')
    lote_produccion_origen = models.ForeignKey('Inv_Producto', on_delete=models.PROTECT,
                                              related_name='solicitudes_envasado')
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2, 
                                             validators=[MinValueValidator(0)])
    
    # Envase a utilizar
    envase = models.ForeignKey('Envase', on_delete=models.PROTECT)
    cantidad_envases = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # Insumos necesarios (JSON field para simplificar)
    insumos_requeridos = models.JSONField(default=list, help_text="Lista de insumos requeridos")
    
    # Resultados del envasado (se llenan al completar)
    producto_destino = models.ForeignKey('Producto_catalogo', on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='solicitudes_envasado_destino')
    lote_destino = models.ForeignKey('Inv_Producto', on_delete=models.PROTECT,
                                    null=True, blank=True,
                                    related_name='solicitudes_envasado_destino')
    
    # Resultados de producción
    unidades_producidas = models.PositiveIntegerField(null=True, blank=True)
    cantidad_perdida = models.DecimalField(max_digits=10, decimal_places=2, 
                                          null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    
    # Consumos reales (JSON field para simplificar)
    consumos_reales = models.JSONField(default=list, blank=True, 
                                      help_text="Lista de consumos reales de insumos")
    
    # Fechas y responsables
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_requerida = models.DateField()
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    solicitante = models.ForeignKey(User, on_delete=models.PROTECT, 
                                   related_name='solicitudes_envasado')
    supervisor_aprueba = models.ForeignKey(User, null=True, blank=True, 
                                         on_delete=models.PROTECT, 
                                         related_name='aprobaciones_envasado')
    responsable_ejecucion = models.ForeignKey(User, null=True, blank=True,
                                             on_delete=models.PROTECT,
                                             related_name='ejecuciones_envasado')
    
    observaciones = models.TextField(blank=True)
    observaciones_proceso = models.TextField(blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        permissions = [
            ('aprobar_envasado', 'Puede aprobar solicitudes de envasado'),
            ('ejecutar_envasado', 'Puede ejecutar el proceso de envasado'),
        ]
    
    def save(self, *args, **kwargs):
        if not self.folio:
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            last_solicitud = SolicitudEnvasado.objects.filter(
                folio__startswith=f'ENV-{year}{month:02d}'
            ).order_by('folio').last()
            
            if last_solicitud:
                last_number = int(last_solicitud.folio.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.folio = f'ENV-{year}{month:02d}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.folio} - {self.producto_granel.nombre_comercial}"

    # views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import *
from .forms import *

@login_required
def lista_solicitudes_envasado(request):
    """Listado de todas las solicitudes"""
    solicitudes = SolicitudEnvasado.objects.all()
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
    
    return render(request, 'envasado/lista_solicitudes.html', {
        'solicitudes': solicitudes,
        'estados': SolicitudEnvasado.ESTADOS
    })

@login_required
def crear_solicitud_envasado(request):
    """Crear nueva solicitud de envasado"""
    if request.method == 'POST':
        form = SolicitudEnvasadoForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = request.user
            solicitud.save()
            form.save_m2m()  # Guardar las presentaciones
            
            messages.success(request, 'Solicitud de envasado creada exitosamente.')
            return redirect('detalle_solicitud_envasado', pk=solicitud.pk)
    else:
        form = SolicitudEnvasadoForm()
    
    return render(request, 'envasado/crear_solicitud.html', {'form': form})

@login_required
def detalle_solicitud_envasado(request, pk):
    """Ver detalle de una solicitud"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    # Verificar disponibilidad de producto a granel
    disponible = solicitud.producto_a_granel.cantidad_actual >= solicitud.cantidad_solicitada
    
    return render(request, 'envasado/detalle_solicitud.html', {
        'solicitud': solicitud,
        'disponible': disponible
    })

@permission_required('envasado.aprobar_envasado')
def aprobar_solicitud_envasado(request, pk):
    """Aprobar una solicitud de envasado"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    if solicitud.estado != 'pendiente':
        messages.error(request, 'Esta solicitud no puede ser aprobada.')
        return redirect('detalle_solicitud_envasado', pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            solicitud.estado = 'aprobada'
            solicitud.supervisor_aprueba = request.user
            solicitud.save()
            
            # Aquí podrías descontar del inventario a granel si es necesario
            # producto_a_granel = solicitud.producto_a_granel
            # producto_a_granel.cantidad_actual -= solicitud.cantidad_solicitada
            # producto_a_granel.save()
            
        messages.success(request, 'Solicitud aprobada exitosamente.')
        return redirect('detalle_solicitud_envasado', pk=pk)
    
    return render(request, 'envasado/aprobar_solicitud.html', {'solicitud': solicitud})

@permission_required('envasado.ejecutar_envasado')
def iniciar_envasado(request, pk):
    """Iniciar el proceso de envasado"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=pk)
    
    if solicitud.estado != 'aprobada':
        messages.error(request, 'Esta solicitud no está aprobada para iniciar.')
        return redirect('detalle_solicitud_envasado', pk=pk)
    
    solicitud.estado = 'en_proceso'
    solicitud.fecha_inicio = timezone.now()
    solicitud.save()
    
    messages.success(request, 'Proceso de envasado iniciado.')
    return redirect('registrar_lote_envasado', solicitud_pk=pk)

@login_required
def registrar_lote_envasado(request, solicitud_pk):
    """Registrar un lote de producto envasado"""
    solicitud = get_object_or_404(SolicitudEnvasado, pk=solicitud_pk)
    
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
                total_envasado = LoteEnvasado.objects.filter(
                    solicitud=solicitud
                ).aggregate(total=models.Sum('cantidad_producida'))['total'] or 0
                
                if total_envasado >= solicitud.cantidad_unidades_totales():
                    solicitud.estado = 'completada'
                    solicitud.fecha_fin = timezone.now()
                    solicitud.save()
                
                messages.success(request, 'Lote registrado exitosamente.')
                return redirect('detalle_solicitud_envasado', pk=solicitud_pk)
    else:
        form = LoteEnvasadoForm(solicitud=solicitud)
    
    return render(request, 'envasado/registrar_lote.html', {
        'form': form,
        'solicitud': solicitud
    })