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

    @login_required
def crear_prueba_quimicaV(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)

    if produccion.pruebas_quimicas.exists():
        return redirect('detalle_prueba_quimica', pk=pk)
        
    if request.method == 'POST':
        # Capturar datos del formulario principal
        fecha_prueba = request.POST.get('fecha_prueba')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None
        observaciones = request.POST.get('observaciones', '')
        
        # Validar fecha de prueba
        if not fecha_prueba:
            messages.error(request, 'La fecha de prueba es obligatoria')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })
        
        # Validar que haya al menos un parametro
        tiene_parametros = False
        for key in request.POST.keys():
            if key.startswith('parametro_'):
                tiene_parametros = True
                break
        
        if not tiene_parametros:
            messages.error(request, 'Debe agregar al menos un parámetro para la prueba')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })

        try:
            # Usar transaccion para asegurar consistencia
            with transaction.atomic():
                # Crear la prueba quimica
                prueba = PruebaQuimica.objects.create(
                    nomenclador_prueba=f"{produccion.lote}-{produccion.catalogo_producto.nombre_comercial}",
                    produccion=produccion,
                    fecha_prueba=fecha_prueba,
                    fecha_vencimiento=fecha_vencimiento,
                    observaciones=observaciones,
                    estado="En Proceso",  # Establecer estado aqui
                    # usuario=request.user
                )

                # Contador de parametros procesados
                parametros_procesados = 0
                errores_validacion = []
                
                # Procesar parametros dinamicos - METODO CORRECTO
                for key in request.POST.keys():
                    if key.startswith('parametro_'):
                        # Extraer el indice del nombre del campo
                        try:
                            index = key.split('_')[1]
                        except IndexError:
                            continue
                        
                        # Obtener valores usando el indice
                        parametro_id = request.POST.get(f'parametro_{index}')
                        valor_medido = request.POST.get(f'valor_medido_{index}')

                        # Validar que tenga valores
                        if not parametro_id or not valor_medido:
                            errores_validacion.append(f'Parametro {index}: Faltan datos')
                            continue
                        else:
                            print(f"  ✓ Datos completos para indice {index}")
                            
                        parametro = ParametroPrueba.objects.filter(id=parametro_id).first()
                        
                        try:
                            parametro = ParametroPrueba.objects.get(id=parametro_id)
                            
                        except ParametroPrueba.DoesNotExist:
                            errores_validacion.append(f'Parámetro {index}: No existe o esta inactivo')
                            continue

                        # Validar valor segun tipo si es numerico.tipo in ['fisico', 'quimico', 'microbiologico']
                        if parametro.tipo in ['fisico', 'quimico', 'microbiologico']:
                            print(f"✓ Parametro no Organoleptico")
                            try:
                                valor_decimal = Decimal(str(valor_medido).replace(',', '.'))
                                
                                # Validar rangos si existen
                                if parametro.valor_minimo is not None and valor_decimal < parametro.valor_minimo:
                                    mensaje = f'Parametro {parametro.nombre}: Valor {valor_medido} debajo del minimo ({parametro.valor_minimo})'
                                    errores_validacion.append(mensaje)
                                    # Puedes decidir si continuar o no
                                
                                if parametro.valor_maximo is not None and valor_decimal > parametro.valor_maximo:
                                    mensaje = f'Parámetro {parametro.nombre}: Valor {valor_medido} sobre el máximo ({parametro.valor_maximo})'
                                    errores_validacion.append(mensaje)
                                    # Puedes decidir si continuar o no
                                    
                            except (InvalidOperation, ValueError):
                                errores_validacion.append(f'Parámetro {parametro.nombre}: Valor "{valor_medido}" no es numérico válido')
                                continue
                        
                        # Crear detalle de prueba química
                        if parametro.tipo in ['fisico', 'quimico', 'microbiologico']:
                            DetallePruebaQuimica.objects.create( 
                                                                prueba=prueba, 
                                                                parametro=parametro, 
                                                                valor_medido=Decimal(valor_medido), 
                                                                )
                        else:
                            DetallePruebaQuimica.objects.create( 
                                                                prueba=prueba,
                                                                parametro=parametro, 
                                                                valor_medido=valor_medido, 
                                                                cumplimiento=False,  
                                                                )
                        
                        parametros_procesados += 1
                
                # Verificar que se procesaron parámetros
                if parametros_procesados == 0:
                    raise ValueError('No se pudieron procesar parámetros. Verifique los datos.')
                
                # Mostrar errores de validación como advertencias
                if errores_validacion:
                    for error in errores_validacion:
                        messages.warning(request, error)
                
                # Mensaje de éxito
                messages.success(request, f'Prueba química creada exitosamente con {parametros_procesados} parámetros')
                
                # Redirigir al detalle de la prueba o a la lista
                return redirect('detalle_prueba_quimica', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error al crear la prueba: {str(e)}')
            # Log del error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error crear_prueba_quimica: {str(e)}', exc_info=True)
            
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })
    
    # GET request - mostrar formulario
    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
        'produccion': produccion,
        'parametros_existentes': parametros_existentes,
    })

#Salva del crear prueba quimica
@login_required
def crear_prueba_quimicaO(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)

    if produccion.pruebas_quimicas.exists():
        return redirect('detalle_prueba_quimica', pk=pk)
        
    if request.method == 'POST':
        # Capturar datos del formulario principal
        fecha_prueba = request.POST.get('fecha_prueba')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None
        observaciones = request.POST.get('observaciones', '')
        
        # Validar fecha de prueba
        if not fecha_prueba:
            messages.error(request, 'La fecha de prueba es obligatoria')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })
        
        # Validar que haya al menos un parámetro
        tiene_parametros = False
        for key in request.POST.keys():
            if key.startswith('parametro_'):
                tiene_parametros = True
                break
        
        if not tiene_parametros:
            messages.error(request, 'Debe agregar al menos un parámetro para la prueba')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })

        try:
            # Usar transacción para asegurar consistencia
            with transaction.atomic():
                # Crear la prueba química
                prueba = PruebaQuimica.objects.create(
                    nomenclador_prueba=f"{produccion.lote}-{produccion.catalogo_producto.nombre_comercial}",
                    produccion=produccion,
                    fecha_prueba=fecha_prueba,
                    fecha_vencimiento=fecha_vencimiento,
                    observaciones=observaciones,
                    estado="En Proceso",
                )
                
                # Contador de parámetros procesados
                parametros_procesados = 0
                errores_validacion = []
                
                # Procesar parámetros dinámicos
                for key in request.POST.keys():
                    if key.startswith('parametro_'):
                        # Extraer el índice
                        index = key.split('_')[1]
                        
                        # Obtener valores
                        parametro_id = request.POST.get(f'parametro_{index}')
                        valor_medido = request.POST.get(f'valor_medido_{index}')
                        
                        if not parametro_id or not valor_medido:
                            errores_validacion.append(f'Parámetro {index}: Faltan datos')
                            continue
                        
                        try:
                            parametro = ParametroPrueba.objects.get(id=parametro_id)
                            
                        except ParametroPrueba.DoesNotExist:
                            errores_validacion.append(f'Parámetro {index}: No existe')
                            continue

                        # Procesar según el tipo de parámetro
                        if parametro.tipo == 'organoleptico':
                            # Para organolépticos, el valor será 'true' o 'false'
                            cumplimiento = valor_medido.lower() == 'true'
                            
                            DetallePruebaQuimica.objects.create(
                                prueba=prueba,
                                parametro=parametro,
                                valor_medido=str(cumplimiento),
                                cumplimiento=cumplimiento,
                            )
                            
                        else:
                            # Para otros tipos
                            try:
                                valor_decimal = Decimal(str(valor_medido).replace(',', '.'))
                                
                                # Validar rangos si existen
                                if parametro.valor_minimo is not None and valor_decimal < parametro.valor_minimo:
                                    errores_validacion.append(f'{parametro.nombre}: Valor debajo del mínimo')
                                
                                if parametro.valor_maximo is not None and valor_decimal > parametro.valor_maximo:
                                    errores_validacion.append(f'{parametro.nombre}: Valor sobre el máximo')
                                    
                            except (InvalidOperation, ValueError):
                                errores_validacion.append(f'{parametro.nombre}: Valor no es numérico válido')
                                continue
                            
                            DetallePruebaQuimica.objects.create(
                                prueba=prueba,
                                parametro=parametro,
                                valor_medido=valor_medido,
                            )
                        
                        parametros_procesados += 1
                
                # Verificar que se procesaron parámetros
                if parametros_procesados == 0:
                    raise ValueError('No se pudieron procesar parámetros')
                
                # Mostrar errores de validación
                if errores_validacion:
                    for error in errores_validacion:
                        messages.warning(request, error)
                
                # Mensaje de éxito
                messages.success(request, f'Prueba creada con {parametros_procesados} parámetros')
                return redirect('detalle_prueba_quimica', pk=pk)
                
        except Exception as e:
            messages.error(request, f'Error al crear la prueba: {str(e)}')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })
    
    # GET request
    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
        'produccion': produccion,
        'parametros_existentes': parametros_existentes,
    })
