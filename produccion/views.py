# views.py
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django.utils import timezone
<<<<<<< Updated upstream
=======
from django.db.models import Q
from decimal import Decimal, InvalidOperation
>>>>>>> Stashed changes
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
    DetallePruebaFormSet, AprobarPruebaForm, ParametroPruebaForm, BuscarParametroForm)

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
        
        print("Datos en sesión 2:", produccion_data)  # Para debug
        
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
<<<<<<< Updated upstream

            # Guardar materias primas
            """ for mp_data in materias_primas:
                Inv_Mat_Prima.objects.create(
                    #produccion=produccion,
                    materia_prima=mp_data['materia_prima'],
                    almacen=mp_data['almacen'],
                    cantidad=mp_data['cantidad']
                ) """
=======
            print(produccion.catalogo_producto)

            #generar un vale de almacen tipo solicitud
            print('Voy a crear vale')
            vale = Vale_Movimiento_Almacen.objects.create(
                tipo = 'Solicitud',
                entrada = False
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
>>>>>>> Stashed changes
            
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

#Este es el que está en uso
def iniciar_produccion(request, pk):
    """View para iniciar una producción específica"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.estado == 'Planificada':
<<<<<<< Updated upstream
        produccion.estado = 'En proceso'
=======
        produccion.estado = 'Iniciando mezcla'
>>>>>>> Stashed changes
        produccion.save()
        messages.success(request, f'✅ Producción {produccion.lote} iniciada correctamente')
    else:
        messages.warning(request, f'⚠️ La producción {produccion.lote} ya está en estado: {produccion.estado}')
    
    return redirect('produccion_list')
<<<<<<< Updated upstream
#Este dió error
"""class CambiarEstadoProduccionView(View):
    def post(self, request, pk):
        produccion_p = get_object_or_404(Produccion, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado:
            estado_anterior = produccion_p.estado
            produccion_p.estado = nuevo_estado
            produccion_p.save()
            
            messages.success(request, f'Estado cambiado de {estado_anterior} a {nuevo_estado}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'estado_actual': produccion_p.estado,
                    'mensaje': f'Estado cambiado exitosamente a {nuevo_estado}'
                })
        
        return redirect('produccion_list')

class ProduccionUpdateView(UpdateView):
    model = Produccion
    form_class = ProduccionForm
    template_name = 'produccion/form.html'
    success_url = reverse_lazy('produccion_list') """
=======

def agita_produccion(request, pk):
    produccion_p = get_object_or_404(Produccion, pk=pk)
        
    if produccion_p.estado == 'Iniciando mezcla':
        produccion_p.estado = 'En proceso: Agitado'
        produccion_p.save()
            
        messages.success(request, f'✅ Producción {produccion_p.lote} actualizada correctamente')
            
    else:
        messages.warning(request, f'⚠️ La producción {produccion_p.lote} ya está en estado: {produccion_p.estado}')
    
    return redirect('produccion_list')
>>>>>>> Stashed changes

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
    
<<<<<<< Updated upstream
    return render(request, 'produccion/concluir_produccion.html', {
        'produccion': produccion
    })
=======
    return render(request, 'produccion/concluir_produccion.html', { 'produccion': produccion })
>>>>>>> Stashed changes

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
    
    if not produccion.pruebas_quimicas:
        messages.error(request, 'No hay archivo de pruebas químicas para descargar')
        return redirect('produccion_list')
    
    # Servir el archivo para descarga
    response = FileResponse(produccion.pruebas_quimicas)
    response['Content-Disposition'] = f'attachment; filename="{produccion.nombre_archivo_pruebas()}"'
    return response

def eliminar_pruebas_quimicas(request, pk):
    """View para eliminar el archivo de pruebas químicas"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.pruebas_quimicas:
        # Eliminar el archivo físico del sistema de archivos
        if os.path.isfile(produccion.pruebas_quimicas.path):
            os.remove(produccion.pruebas_quimicas.path)
        
        # Limpiar el campo en la base de datos
        produccion.pruebas_quimicas.delete(save=False)
        produccion.pruebas_quimicas = None
        produccion.save()
        
        messages.success(request, f'✅ Archivo de pruebas químicas eliminado para {produccion.lote}')
    else:
        messages.warning(request, 'No hay archivo para eliminar')
    
    return redirect('produccion_list')

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

###---Registro de pruebas químicas---###

@login_required
#@permission_required('produccion.add_pruebaquimica')
def crear_prueba_quimica_base(request, pk):
    """Crear una nueva prueba química para una producción específica"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    # Obtener parámetros existentes para el select
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)
    
    if request.method == 'POST':
        form = PruebaQuimicaForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Validar fecha de prueba
                fecha_prueba_str = request.POST.get('fecha_prueba')
                if not fecha_prueba_str:
                    messages.error(request, 'La fecha de prueba es obligatoria')
                    return render(request, 'produccion/crear_prueba_quimica.html', {
                        'produccion': produccion,
                        'form': form,
                        'parametros_existentes': parametros_existentes
                    })
                
                # Convertir fecha de prueba
                from django.utils.dateparse import parse_datetime
                fecha_prueba = parse_datetime(fecha_prueba_str)
                if not fecha_prueba:
                    messages.error(request, 'Formato de fecha inválido')
                    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                        'produccion': produccion,
                        'form': form,
                        'parametros_existentes': parametros_existentes
                    })
                
                # Crear la prueba química
                prueba = form.save(commit=False)
                prueba.produccion = produccion
                prueba.fecha_prueba = fecha_prueba
                prueba.save()
                
                # Procesar parámetros del formulario
                parametros_ids = request.POST.getlist('parametro')
                valores = request.POST.getlist('valor_medido')
                observaciones = request.POST.getlist('observaciones_parametro')
                
                # Validar que haya al menos un parámetro
                if not parametros_ids or not any(parametros_ids):
                    messages.error(request, 'Debe agregar al menos un parámetro')
                    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                        'produccion': produccion,
                        'form': form,
                        'parametros_existentes': parametros_existentes
                    })
                
                # Guardar cada parámetro
                for i in range(len(parametros_ids)):
                    if parametros_ids[i]:  # Solo procesar si hay parámetro seleccionado
                        try:
                            parametro = ParametroPrueba.objects.get(id=parametros_ids[i])
                            
                            # Crear detalle de prueba
                            DetallePruebaQuimica.objects.create(
                                prueba=prueba,
                                parametro=parametro,
                                valor_medido=valores[i] if i < len(valores) else '',
                                observaciones=observaciones[i] if i < len(observaciones) else ''
                            )
                        except ParametroPrueba.DoesNotExist:
                            messages.error(request, f'Parámetro con ID {parametros_ids[i]} no existe')
                            continue
                
                # Calcular resultado final
                prueba.resultado_final = prueba.calcular_resultado_final()
                prueba.save()
                
                messages.success(request, f'Prueba química creada exitosamente para lote {produccion.lote}')
                return redirect('produccion_list')
                
            except Exception as e:
                messages.error(request, f'Error al crear la prueba: {str(e)}')
    else:
        form = PruebaQuimicaForm()
    
    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
        'produccion': produccion,
        'form': form,
        'parametros_existentes': parametros_existentes
    })

def crear_prueba_quimica(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)
    
    if request.method == 'POST':
        # Capturar datos del formulario principal
        fecha_prueba = request.POST.get('fecha_prueba')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None
        observaciones = request.POST.get('observaciones', '')
        
        # Validar fecha de prueba
        if not fecha_prueba:
            return render(request, 'produccion/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
                'error': 'La fecha de prueba es obligatoria'
            })
        
        # Crear la prueba química
        prueba = PruebaQuimica.objects.create(
            produccion=produccion,
            fecha_prueba=fecha_prueba,
            fecha_vencimiento=fecha_vencimiento,
            observaciones=observaciones,
            usuario=request.user
        )
        
        # Procesar parámetros dinámicos
        contador = 1
        while True:
            parametro_id = request.POST.get(f'parametro_{contador}')
            valor_medido = request.POST.get(f'valor_medido_{contador}')
            
            if not parametro_id or not valor_medido:
                break
            
            try:
                parametro = ParametroPrueba.objects.get(id=parametro_id)
                
                # Validar valor según tipo
                if parametro.tipo_valor == 'numerico':
                    try:
                        valor_decimal = Decimal(valor_medido)
                        
                        # Validar rangos si existen
                        if parametro.valor_minimo and valor_decimal < parametro.valor_minimo:
                            # Podrías registrar esto como advertencia
                            pass
                        
                        if parametro.valor_maximo and valor_decimal > parametro.valor_maximo:
                            # Podrías registrar esto como advertencia
                            pass
                            
                    except (InvalidOperation, ValueError):
                        # Valor no es decimal válido
                        pass
                
                # Crear parámetro de prueba
                observacion_param = request.POST.get(f'observacion_param_{contador}', '')
                
                ParametroPrueba.objects.create(
                    prueba=prueba,
                    parametro=parametro,
                    valor_medido=valor_medido,
                    observaciones=observacion_param,
                    dentro_especificacion=parametro.validar_valor(valor_medido)
                )
                
            except ParametroPrueba.DoesNotExist:
                pass
            
            contador += 1
        
        return redirect('produccion_list')
    
    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
        'produccion': produccion,
        'parametros_existentes': parametros_existentes,
    })

@login_required
def detalle_prueba_quimica(request, prueba_id):
    """Ver detalle de una prueba química"""
    prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
    detalles = prueba.detalles.select_related('parametro')
    
    return render(request, 'produccion/detalle_prueba_quimica.html', {
        'prueba': prueba,
        'detalles': detalles
    })

@login_required
@permission_required('produccion.change_pruebaquimica')
def aprobar_prueba_quimica(request, prueba_id):
    """Aprobar o rechazar una prueba química"""
    prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
    
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
    
    return render(request, 'produccion/aprobar_prueba_quimica.html', {
        'prueba': prueba,
        'form': form
    })

# views.py

@login_required
@permission_required('produccion.view_parametroprueba')
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
@permission_required('produccion.add_parametroprueba')
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
@permission_required('produccion.change_parametroprueba')
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