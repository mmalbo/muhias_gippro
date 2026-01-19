# views.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from decimal import Decimal, InvalidOperation
import datetime
import json

from collections import OrderedDict
from .models import Produccion, Prod_Inv_MP, PruebaQuimica, ParametroPrueba, DetallePruebaQuimica
from materia_prima.models import MateriaPrima
from inventario.models import Inv_Mat_Prima
from producto.models import Producto
from envase_embalaje.models import Formato
from nomencladores.almacen.models import Almacen
from movimientos.models import Vale_Movimiento_Almacen
from .forms import (ProduccionForm, MateriaPrimaForm, 
    SubirPruebasQuimicasForm, CancelarProduccionForm, PruebaQuimicaForm, 
    DetallePruebaForm, AprobarPruebaForm, ParametroPruebaForm, BuscarParametroForm)

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
            # Procesar producto (existente o nuevo)
            catalogo_producto_id = self.procesar_producto(request)
            if not catalogo_producto_id:
                return JsonResponse({
                    'success': False, 
                    'errors': 'Error al procesar el producto'
                })
            
            # Extraer solo datos primitivos para la sesión
            session_data = {
                'lote': request.POST.get('lote'),
                'catalogo_producto_id': str(catalogo_producto_id),  # Guardar como string
                'cantidad_estimada': request.POST.get('cantidad_estimada'),
                'costo': request.POST.get('costo'),
                'prod_result': request.POST.get('prod_result'),
                'planta_id': request.POST.get('planta'),  # Guardar el ID como string
            }            
            # Guardar en sesión
            request.session['produccion_data'] = session_data
            request.session.modified = True
            return JsonResponse({'success': True, 'step': 2})
        else:
            print("❌ Errores en formulario:", produccion_form.errors)
            return JsonResponse({'success': False, 'errors': produccion_form.errors})

    def procesar_producto(self, request):
        """Procesa el producto (existente o nuevo) y retorna el ID"""
        nuevo_producto_nombre = request.POST.get('nuevo_producto_nombre')
        catalogo_producto_id = request.POST.get('catalogo_producto')

        if nuevo_producto_nombre:
            # Crear nuevo producto en el catálogo
            try:
                formato_agranel = Formato.objects.filter(capacidad=0).first()

                # Crear en CatalogoProducto (no en Producto)
                catalogo_producto = Producto.objects.create(
                    nombre_comercial=nuevo_producto_nombre.strip(),
                    formato=formato_agranel,
                    estado="produccion",
                    costo=0
                )
                return catalogo_producto.id
                
            except Exception as e:
                print(f"Error al crear producto: {e}")
                return None
        elif catalogo_producto_id:
            # Usar producto existente - verificar que existe
            try:
                catalogo_producto = Producto.objects.get(id=catalogo_producto_id)
                return catalogo_producto_id
            except Producto.DoesNotExist:
                print(f"❌ Producto con ID {catalogo_producto_id} no existe")
                return None
        else:
            print("❌ No se proporcionó ni nuevo producto ni producto existente")
            return None

    def procesar_paso_2(self, request):
        # Recuperar datos del paso 1 de la sesión
        
        produccion_data = request.session.get('produccion_data', {})
        
        if not produccion_data:
            return JsonResponse({
                'success': False, 
                'errors': 'Datos de producción no encontrados. Por favor, complete el paso 1 nuevamente.'
            })
            
        # Verificar que los datos mínimos estén presentes
        required_fields = ['lote', 'catalogo_producto_id', 'cantidad_estimada', 'costo', 'planta_id']
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
            print(f"🔍 Buscando catalogo_producto con ID: {produccion_data['catalogo_producto_id']}")
            catalogo_producto_instance = Producto.objects.get(id=produccion_data['catalogo_producto_id'])
            print(f"✅ Producto encontrado: {catalogo_producto_instance.nombre_comercial}")

            if produccion_data['prod_result']: 
                product=True
            else:
                product=False

            print(f"✅ Producto base: {product}" )
            # Guardar producción
            produccion = Produccion.objects.create(
                lote=produccion_data['lote'],
                catalogo_producto=catalogo_producto_instance,
                prod_result=product,
                cantidad_estimada=produccion_data['cantidad_estimada'],
                costo=produccion_data['costo'],                
                planta=planta_instance,
                estado='Planificada'
            )
            print(produccion.lote)
            print(produccion.catalogo_producto)

            #generar un vale de almacen tipo solicitud
            print('Voy a crear vale')
            id_almacen = materias_primas[0]['almacen']
            print(id_almacen.id)
            vale = Vale_Movimiento_Almacen.objects.create(
                tipo = 'Solicitud',
                entrada = False,
                almacen = id_almacen
            )
            print(vale.tipo)

            # Guardar relación con materias primas
            for mp_data in materias_primas:
                if not vale.almacen:
                    vale.almacen = mp_data['almacen']
                Prod_Inv_MP.objects.create(
                    lote_prod=produccion,
                    inv_materia_prima=mp_data['materia_prima'],
                    cantidad_materia_prima=mp_data['cantidad'],
                    almacen=mp_data['almacen'],
                    vale = vale
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

#Flujo básico de la producción
def iniciar_produccion(request, pk):
    """View para iniciar una producción específica"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.estado == 'Planificada':
        produccion.estado = 'En proceso: Iniciando mezcla'
        produccion.save()
        messages.success(request, f'✅ Producción {produccion.lote} iniciada correctamente')
    else:
        messages.warning(request, f'⚠️ La producción {produccion.lote} ya está en estado: {produccion.estado}')
    
    return redirect('produccion_list')

def agita_produccion(request, pk):
    produccion_p = get_object_or_404(Produccion, pk=pk)
        
    if produccion_p.estado == 'En proceso: Iniciando mezcla':
        produccion_p.estado = 'En proceso: Agitado'
        produccion_p.save()
            
        messages.success(request, f'✅ Producción {produccion_p.lote} actualizada correctamente')
            
    else:
        messages.warning(request, f'⚠️ La producción {produccion_p.lote} ya está en estado: {produccion_p.estado}')
    
    return redirect('produccion_list')

def concluir_produccion(request, pk):
    """View para mostrar formulario de conclusión"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if request.method == 'POST' and produccion.estado == 'En proceso: Agitado':
        cantidad_real = request.POST.get('cantidad_real')
        
        if cantidad_real:
            try:
                cantidad_real = float(cantidad_real)
                if cantidad_real > 0:
                    produccion.cantidad_real = cantidad_real
                    produccion.estado = 'En proceso: Validación'
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
    
    return render(request, 'produccion/concluir_produccion.html', { 'produccion': produccion })

def cancelar_produccion(request, pk):
    """View para cancelar una producción con observaciones"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    # Verificar si puede ser cancelada
    if not produccion.puede_ser_cancelada():
        messages.error(request, f'❌ No se puede cancelar la producción {produccion.lote} porque ya está {produccion.get_estado_display().lower()}')
        return redirect('produccion_list')
    
    if request.method == 'POST':
        form = CancelarProduccionForm(request.POST, produccion=produccion)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Producción {produccion.lote} cancelada correctamente')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Producción cancelada correctamente',
                    'nuevo_estado': produccion.estado
                })
            
            return redirect('produccion_list')
        else:
            messages.error(request, '❌ Error al cancelar la producción')
    else:
        form = CancelarProduccionForm(produccion=produccion)
    
    return render(request, 'produccion/cancelar_produccion.html', {
        'produccion': produccion,
        'form': form
    })

# View para ver detalles de cancelación
def detalle_cancelacion(request, pk):
    """View para ver los detalles de una producción cancelada"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.estado != 'Cancelada':
        messages.warning(request, 'Esta producción no está cancelada')
        return redirect('produccion_list')
    
    return render(request, 'produccion/detalle_cancelacion.html', {
        'produccion': produccion
    })

#funcionalidades para insertar pruebas químicas externas, emitidas por archivo.
def subir_pruebas_quimicas(request, pk):
    """View para subir archivo de pruebas químicas"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if request.method == 'POST':
        form = SubirPruebasQuimicasForm(request.POST, request.FILES, instance=produccion)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Archivo de pruebas químicas subido correctamente para {produccion.lote}')
            produccion.estado = 'Evaluada'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Archivo subido correctamente',
                    'nombre_archivo': produccion.nombre_archivo_pruebas()
                })
            
            return redirect('produccion_list')
        else:
            messages.error(request, '❌ Error al subir el archivo')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': form.errors
                })
    else:
        form = SubirPruebasQuimicasForm(instance=produccion)
    
    return render(request, 'produccion/subir_pruebas.html', {
        'produccion': produccion,
        'form': form
    })

def descargar_pruebas_quimicas(request, pk):
    """View para descargar el archivo de pruebas químicas"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if not produccion.pruebas_quimicas_ext:
        messages.error(request, 'No hay archivo de pruebas químicas para descargar')
        return redirect('produccion_list')
    
    # Servir el archivo para descarga
    response = FileResponse(produccion.pruebas_quimicas_ext)
    response['Content-Disposition'] = f'attachment; filename="{produccion.nombre_archivo_pruebas()}"'
    return response

def eliminar_pruebas_quimicas(request, pk):
    """View para eliminar el archivo de pruebas químicas"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.pruebas_quimicas_ext:
        # Eliminar el archivo físico del sistema de archivos
        if os.path.isfile(produccion.pruebas_quimicas_ext.path):
            os.remove(produccion.pruebas_quimicas_ext.path)
        
        # Limpiar el campo en la base de datos
        produccion.pruebas_quimicas_ext.delete(save=False)
        produccion.pruebas_quimicas_ext = None
        produccion.save()
        
        messages.success(request, f'✅ Archivo de pruebas químicas eliminado para {produccion.lote}')
    else:
        messages.warning(request, 'No hay archivo para eliminar')
    
    return redirect('produccion_list')

###---Registro de pruebas químicas---###
def crear_prueba_quimica(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)

    if produccion.pruebas_quimicas.exists():
        return redirect('detalle_prueba_quimica', pk=pk)
    else:
        print("No existe")
    
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

        if tiene_parametros:
            print("Confirmar parámetros")
        
        try:
            print("-----")
            # Usar transacción para asegurar consistencia
            with transaction.atomic():
                # Crear la prueba química
                prueba = PruebaQuimica.objects.create(
                    nomenclador_prueba=f"{produccion.lote}-{produccion.catalogo_producto.nombre_comercial}",
                    produccion=produccion,
                    fecha_prueba=fecha_prueba,
                    fecha_vencimiento=fecha_vencimiento,
                    observaciones=observaciones,
                    estado="En Proceso",  # Establecer estado aquí
                    # usuario=request.user
                )
                print("-----")
                print(f"✓ Prueba creada: {prueba.nomenclador_prueba} (ID: {prueba.id})")
                print("--XXX--")
                
                # Contador de parámetros procesados
                parametros_procesados = 0
                errores_validacion = []
                
                # Procesar parámetros dinámicos
                print("\n=== Procesando parámetros ===")
                # Procesar parámetros dinámicos - MÉTODO CORRECTO
                for key in request.POST.keys():
                    if key.startswith('parametro_'):
                        print(f"\n📋 Procesando campo: {key}")
                        # Extraer el índice del nombre del campo
                        try:
                            index = key.split('_')[1]
                            print(f"  Índice extraído: {index}")
                        except IndexError:
                            continue
                        
                        # Obtener valores usando el índice
                        parametro_id = request.POST.get(f'parametro_{index}')
                        valor_medido = request.POST.get(f'valor_medido_{index}')

                        print(f"  parametro_{index}: {parametro_id}")
                        print(f"  valor_medido_{index}: {valor_medido}")
                        
                        # Validar que tenga valores
                        if not parametro_id or not valor_medido:
                            errores_validacion.append(f'Parámetro {index}: Faltan datos')
                            continue
                        else:
                            print(f"  ✓ Datos completos para índice {index}")
                            
                        parametro = ParametroPrueba.objects.filter(id=parametro_id).first()
                        print(f"  ✓ Parámetro encontrado: {parametro.nombre} (ID: {parametro.id})")
                        
                        try:
                            parametro = ParametroPrueba.objects.get(id=parametro_id)
                            print("Dentro del TRY")
                            print(parametro.nombre)
                        except ParametroPrueba.DoesNotExist:
                            errores_validacion.append(f'Parámetro {index}: No existe o está inactivo')
                            continue

                        print(parametro.tipo)
                        # Validar valor según tipo si es numérico.tipo in ['fisico', 'quimico', 'microbiologico']
                        if parametro.tipo in ['fisico', 'quimico', 'microbiologico']:
                            print(f"✓ Parametro no Organoléptico")
                            try:
                                valor_decimal = Decimal(str(valor_medido).replace(',', '.'))
                                
                                # Validar rangos si existen
                                if parametro.valor_minimo is not None and valor_decimal < parametro.valor_minimo:
                                    mensaje = f'Parámetro {parametro.nombre}: Valor {valor_medido} debajo del mínimo ({parametro.valor_minimo})'
                                    errores_validacion.append(mensaje)
                                    # Puedes decidir si continuar o no
                                
                                if parametro.valor_maximo is not None and valor_decimal > parametro.valor_maximo:
                                    mensaje = f'Parámetro {parametro.nombre}: Valor {valor_medido} sobre el máximo ({parametro.valor_maximo})'
                                    errores_validacion.append(mensaje)
                                    # Puedes decidir si continuar o no
                                    
                            except (InvalidOperation, ValueError):
                                errores_validacion.append(f'Parámetro {parametro.nombre}: Valor "{valor_medido}" no es numérico válido')
                                continue
                        else:
                            print(f"No entró al if porque es Organole...")
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
                # O si prefieres volver a la lista de producciones:
                # return redirect('produccion_list')
                
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

@login_required
def detalle_prueba_quimica(request, pk):
    """Ver detalle de una prueba química"""
    produccion = get_object_or_404(Produccion, id=pk)

    prueba = get_object_or_404(PruebaQuimica, produccion=produccion.id)

    parametros_disponibles = ParametroPrueba.objects.all()

    # Calcular resumen automático
    parametros = DetallePruebaQuimica.objects.filter(prueba=prueba).all()
    total_parametros = parametros.count()
    parametros_aprobados = parametros.filter(cumplimiento=True).count()
    parametros_rechazados = total_parametros - parametros_aprobados
    
    porcentaje_aprobacion = 0
    if total_parametros > 0:
        porcentaje_aprobacion = round((parametros_aprobados / total_parametros) * 100, 2)
    
    context = {
        'prueba': prueba,
        'parametros': parametros,
        'total_parametros': total_parametros,
        'parametros_aprobados': parametros_aprobados,
        'parametros_rechazados': parametros_rechazados,
        'porcentaje_aprobacion': porcentaje_aprobacion,
        'parametros_disponibles': parametros_disponibles,
    }
    
    return render(request, 'produccion/prueba_quimica/detalle_prueba_quimica.html', context)

@login_required
def aprobar_prueba_quimica(request, pk):
    """Aprobar o rechazar una prueba química"""    
    prueba = get_object_or_404(PruebaQuimica, pk=pk)
    
    if request.method == 'POST':
        form = AprobarPruebaForm(request.POST)
        accion = request.POST.get('accion')
        
        if form.is_valid():
            if accion == 'aprobar':
                prueba.aprobar(request.user)
                messages.success(request, 'Prueba aprobada correctamente')
            elif accion == 'rechazar':
                prueba.rechazar(request.user)
                messages.warning(request, 'Prueba rechazada')
            
            return redirect('detalle_prueba_quimica', prueba_id=prueba.id)
    else:
        form = AprobarPruebaForm()
    
    return render(request, 'produccion/prueba_quimica/aprobar_prueba_quimica.html', {
        'prueba': prueba,
        'form': form
    })

#Gestión de parámetros como nomencladores
@login_required
def lista_parametros(request):
    """Lista y busca parámetros con filtros avanzados"""
    form = BuscarParametroForm(request.GET or None)
    parametros = ParametroPrueba.objects.all()
    
    """if form.is_valid():
        tipo = form.cleaned_data.get('tipo')
        activo = form.cleaned_data.get('activo')
        buscar = form.cleaned_data.get('buscar')
        
        if tipo:
            parametros = parametros.filter(tipo=tipo)
        if activo == 'true':
            parametros = parametros.filter(activo=True)
        elif activo == 'false':
            parametros = parametros.filter(activo=False)
        if buscar:
            parametros = parametros.filter(
                Q(nombre__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
    
    parametros = parametros.select_related('tipo').order_by('tipo', 'nombre')"""
    
    return render(request, 'produccion/parametros/list.html', {
        'parametros': parametros,
        'form': form
    })

@login_required
def crear_parametro(request):
    """Crear nuevo parámetro personalizado"""
    if request.method == 'POST':
        form = ParametroPruebaForm(request.POST)
        if form.is_valid():
            parametro = form.save()
            messages.success(request, f'Parámetro {parametro.nombre} creado exitosamente')
            return redirect('parametros_lista')
    else:
        form = ParametroPruebaForm()
    
    return render(request, 'produccion/parametros/crear_parametro.html', {'form': form})

@login_required
def editar_parametro(request, parametro_id):
    """Editar parámetro existente"""
    parametro = get_object_or_404(ParametroPrueba, id=parametro_id)
    
    if request.method == 'POST':
        form = ParametroPruebaForm(request.POST, instance=parametro)
        if form.is_valid():
            parametro = form.save()
            messages.success(request, f'Parámetro {parametro.nombre} actualizado')
            return redirect('parametros_lista')
    else:
        # Convertir lista de opciones a texto separado por líneas
        initial = {}
               
        form = ParametroPruebaForm(instance=parametro, initial=initial)
    
    return render(request, 'produccion/parametros/crear_parametro.html', {
        'form': form,
        'parametro': parametro
    })

@login_required
def detalle_parametro(request, parametro_id):
    """Ver detalle completo de un parámetro"""
    parametro = get_object_or_404(ParametroPrueba, id=parametro_id)
    
    return render(request, 'produccion/parametros/detalle_parametro.html', {
        'parametro': parametro,
    })

#Gestión parámetros de una prueba química
@login_required
def agregar_parametros_prueba_ant(request, prueba_id):
    try:
        """Agregar múltiples parámetros a una prueba"""
        prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
        print("-----")
        print(f"✓ Prueba: {prueba.nomenclador_prueba}")
        print("--XXX--")

        parametros_data = request.POST.get('parametros')
        #data = json.loads(request.POST.get('parametros', '[]'))
        # DEBUG: Ver qué está llegando
        print("=== DEBUG RECEPCIÓN DE DATOS ===")
        print(f"Request method: {request.method}")
        print(f"Request POST: {request.POST}")
        print(f"Request body: {request.body}")
        print(f"parametros_data: {parametros_data}")
        print("================================")

        if not parametros_data:
            return JsonResponse({
                'success': False,
                'message': 'No se recibieron datos de parámetros'
            })
        
        # Parsear JSON
        try:
            print("Estoy aqui dentro")
            parametros = json.loads(parametros_data)
        except json.JSONDecodeError as e:
            print("fallo")
            return JsonResponse({
                'success': False,
                'message': f'Error en formato JSON: {str(e)}'
            })
        print("--XXX--")
        print(parametros)
        print("--XXX--")
        for item in parametros:
            parametro = get_object_or_404(ParametroPrueba, id=item['parametro_id'])
            print(f"✓ Parametro: {parametro.nombre}")
            print(f"✓ Parametro: {parametro.tipo}")
            # Crear nuevo parámetro de prueba
            if parametro.es_numerico:
                DetallePruebaQuimica.objects.create(
                    prueba=prueba, 
                    parametro=parametro, 
                    valor_medido=item['valor_medido'],
                    observaciones=item.get('observaciones', '')
                )
            else:
                DetallePruebaQuimica.objects.create(
                    prueba=prueba, 
                    parametro=parametro, 
                    valor_medido=item['valor_medido'],
                    cumplimiento=item['cumplimiento'],
                    observaciones=item.get('observaciones', '')
                )                
        
        return JsonResponse({
            'success': True,
            'message': f'{len(data)} parámetros agregados correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def agregar_parametros_prueba(request, prueba_id):
    """
    View para agregar múltiples parámetros a una prueba química
    """
    # Obtener la prueba
    try:
        prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
        
    except PruebaQuimica.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'La prueba con ID {prueba_id} no existe'
        }, status=404)
    
    try:
        # Obtener datos JSON del body
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
                parametros = data.get('parametros', [])
                
            except json.JSONDecodeError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error en formato JSON: {str(e)}'
                }, status=400)
        else:
            # Intentar obtener de POST también
            parametros_data = request.POST.get('parametros')
            if parametros_data:
                try:
                    parametros = json.loads(parametros_data)
                    
                except:
                    parametros = []
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de datos no soportado. Use JSON.'
                }, status=400)
        
        # Validar que hay parámetros
        if not parametros or len(parametros) == 0:
            return JsonResponse({
                'success': False,
                'message': 'No se recibieron datos de parámetros'
            }, status=400)
        
        # Validar estructura de cada parámetro
        for i, param in enumerate(parametros):
            if 'parametro_id' not in param or 'valor_medido' not in param:
                return JsonResponse({
                    'success': False,
                    'message': f'Parámetro {i+1} incompleto. Faltan campos requeridos.'
                }, status=400)
        
        # Crear parámetros
        parametros_creados = []
        errores = []
        
        for i, param in enumerate(parametros):
            try:
                parametro_id = param['parametro_id']
                valor_medido = param['valor_medido']
                observaciones = param.get('observaciones', '')

                # Obtener el objeto Parametro
                try:
                    parametro_obj = ParametroPrueba.objects.get(id=parametro_id)
                    
                except ParametroPrueba.DoesNotExist:
                    errores.append(f"Parámetro ID {parametro_id} no existe")
                    continue
               
                # Crear ParametroPruebaQuimica
                if parametro_obj.tipo in ['fisico', 'quimico', 'microbiologico']:
                    param_prueba = DetallePruebaQuimica.objects.create(
                        prueba=prueba, 
                        parametro=parametro_obj, 
                        valor_medido=Decimal(valor_medido),
                        observaciones=observaciones
                    )
                else:
                    param_prueba = DetallePruebaQuimica.objects.create(
                        prueba=prueba, 
                        parametro=parametro_obj, 
                        valor_medido=valor_medido,
                        cumplimiento=False,
                        observaciones=observaciones
                    )
                
                parametros_creados.append({
                    'id': param_prueba.id,
                    'nombre': parametro_obj.nombre,
                    'valor': valor_medido,
                    'unidad': parametro_obj.unidad_medida or ''
                })
                
            except Exception as e:
                error_msg = f"Error en parámetro {i+1}: {str(e)}"
                errores.append(error_msg)
                
        if errores:
            return JsonResponse({
                'success': False,
                'message': 'Algunos parámetros no pudieron crearse',
                'errores': errores,
                'creados': parametros_creados
            })
        
        
        return JsonResponse({
            'success': True,
            'message': f'Se agregaron {len(parametros_creados)} parámetros correctamente',
            'parametros': parametros_creados,
            #'total_parametros': prueba.parametros_creados.count()
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'message': f'Error inesperado: {str(e)}'
        }, status=500)

@login_required
def editar_parametro_prueba(request, pk):
    """Editar valor de un parámetro existente"""
    parametro_prueba = get_object_or_404(DetallePruebaQuimica, id=pk)
    try:
        nuevo_valor = request.POST.get('valor_medido', '').strip()
        if not nuevo_valor:
            return JsonResponse({
                'success': False,
                'message': 'El valor no puede estar vacío'
            })

        parametro_prueba.valor_medido = Decimal(nuevo_valor.replace(',','.'))

        parametro_prueba.save()
        print(parametro_prueba.valor_medido)
        print(parametro_prueba.parametro.valor_minimo)
        print(parametro_prueba.parametro.valor_maximo)
        
        # Calcular si está dentro de especificación
        #dentro_especificacion = parametro.verificar_especificacion()
        
        return JsonResponse({
            'success': True,
            #'dentro_especificacion': dentro_especificacion,
            'message': 'Valor actualizado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def eliminar_parametro_prueba(request, parametro_id):
    """Eliminar un parámetro de prueba"""
    parametro = get_object_or_404(ParametroPrueba, id=parametro_id)
    
    try:
        parametro.delete()
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def concluir_prueba(request, pk):
    prueba = get_object_or_404(PruebaQuimica, id=pk)
                
    if prueba.estado in ['APROBADA', 'RECHAZADA', 'CANCELADA']:
        messages.error(request, 'Esta prueba ya ha sido concluida anteriormente.')
        return render(request, 'produccion/prueba_quimica/detalle_prueba_quimica.html', {
            'prueba': prueba,
            'parametros': prueba.detalles.all(),
            'error': True
        })
    
    # Obtener datos del formulario
    decision_final = request.POST.get('decision_final')
    observaciones_generales = request.POST.get('observaciones_generales', '')

    # Validaciones
    if not decision_final:
        messages.error(request, 'Debe seleccionar una decisión final.')
        return render(request, 'produccion/detalle_prueba_quimica.html', {
            'prueba': prueba,
            'parametros': prueba.detalles.all(),
            'error': True
        })
    
    try:
        # Actualizar prueba
        prueba.estado = decision_final
        if prueba.estado == 'Aprobada':
            prueba.resultado_final = True
            prueba.produccion.estado = 'Concluida-Satisfactoria'
            prueba.produccion.save()
        elif prueba.estado == 'Rechazada':
            prueba.resultado_final = False
            prueba.produccion.estado = 'Concluida-Rechazada'
            prueba.produccion.save() 
        prueba.observaciones = observaciones_generales
        #prueba.evaluado_por = request.user
        prueba.fecha_aprobacion = timezone.now()
        
        # Si hay parámetros específicos con observaciones
        for key, value in request.POST.items():
            if key.startswith('observaciones_'):
                detalle_id = key.replace('observaciones_', '')
                if detalle_id != 'generales':
                    try:
                        detalle = DetallePruebaQuimica.objects.get(id=detalle_id, prueba=prueba)
                        detalle.observaciones = value
                        detalle.save()
                    except DetallePruebaQuimica.DoesNotExist:
                        continue

        prueba.save()       
        # Mensaje de éxito
        #messages.success(request, f'Prueba {decision_final.lower()} correctamente.')
        # Redirigir a la página de detalle //redirect('detalle_prueba_quimica', pk=prueba.produccion.id)
        #return redirect('produccion_list')
        return JsonResponse({
            'success': True,
            'message': f'Prueba {prueba.estado.lower()} correctamente.',
            'redirect_url': reverse('detalle_prueba_quimica', args=[prueba.produccion.id])
        })    
        
    except Exception as e:
        messages.error(request, f'Error al concluir la prueba: {str(e)}')
        return render(request, 'produccion/prueba_quimica/detalle_prueba_quimica.html', {
            'prueba': prueba,
            'parametros': prueba.detalles.all(),
            'error': True
        })

@login_required
def calcular_resultados_prueba(request, prueba_id):
    """Recalcular resultados de todos los parámetros"""
    prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
    detal_prueba = DetallePruebaQuimica.objects.filter(prueba=prueba).all()
    print(detal_prueba)
    try:
        parametros = []
        aprobados = 0
        rechazados = 0
        
        for parametro in detal_prueba:
            # Recalcular especificación
            dentro = parametro.verificar_especificacion()
            
            if dentro:
                aprobados += 1
            else:
                rechazados += 1
            
            parametros.append({
                'id': parametro.id,
                'dentro_especificacion': dentro
            })
        
        return JsonResponse({
            'success': True,
            'aprobados': aprobados,
            'rechazados': rechazados,
            'parametros': parametros
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)