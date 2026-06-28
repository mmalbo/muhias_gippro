# views.py
import os
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, F, FloatField
from django.db import transaction
from django.db.models.functions import Coalesce
from decimal import Decimal, InvalidOperation
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from django.core.serializers.json import DjangoJSONEncoder
import urllib.parse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import OrderedDict

from .models import Planta
from .models import Produccion, Prod_Inv_MP, PruebaQuimica, ParametroPrueba, DetallePruebaQuimica, Prod_Inv_Producto
from materia_prima.models import MateriaPrima
from inventario.models import Inv_Mat_Prima, Inv_Producto
from producto.models import Producto
from envase_embalaje.models import Formato
from nomencladores.almacen.models import Almacen
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_Prod, Movimiento_MP, Movimiento_EE, Movimiento_Ins
from utils.utils import normalizar_UUID
from .forms import (ProduccionForm, MateriaPrimaForm, 
    SubirPruebasQuimicasForm, CancelarProduccionForm, PruebaQuimicaForm, 
    DetallePruebaForm, AprobarPruebaForm, ParametroPruebaForm, BuscarParametroForm)
from utils.models import Notification

class ProduccionListView(LoginRequiredMixin, ListView):
    model = Produccion
    template_name = 'produccion/list.html'
    context_object_name = 'produccions'
    # Opción A: Usando ordering en la vista
    ordering = ['-fecha_creacion']

class ProduccionDeleteView(LoginRequiredMixin, DeleteView):
    model = Produccion
    template_name = 'produccion/confirm_delete.html'
    success_url = reverse_lazy('produccion_list')

@method_decorator(csrf_exempt, name='dispatch')
class CrearProduccionView(LoginRequiredMixin, View):
    template_name = 'produccion/crear_produccion.html'
    
    def get(self, request):
        produccion_form = ProduccionForm()
        materia_prima_form = MateriaPrimaForm()
    
        # Inicializar sesión si no existe
        if 'produccion_data' not in request.session:
            request.session['produccion_data'] = {}

        # VERIFICAR SI VIENEN DATOS PRE-CARGADOS (de reutilización)
        datos_precargados = self._obtener_datos_precargados(request)

        # Si hay datos pre-cargados, guardarlos en sesión para el paso 1
        if datos_precargados:
            request.session['produccion_data'].update(datos_precargados)
            request.session.modified = True
            
            # Mensaje informativo
            messages.info(
                request, 
                f'Reutilizando produccion {datos_precargados.get("produccion_base_lote", "")}. '
                'Los datos han sido pre-cargados.'
            )
    
        # --- PRODUCTOS PARA INSUMOS (catálogo) ---
        # Filtramos productos en estado 'aprobado' (disponibles para consumir como insumo)
        # También se podría incluir 'terminado' según tu flujo
        productos = Inv_Producto.objects.all().values(
            'id', 'producto__nombre_comercial', 'producto__costo', 'formato__unidad_medida', 'formato__capacidad'
        )
        productos_data = []
        for prod in productos:
            # Determinar unidad de medida según el formato
            if prod.get('formato__capacidad') and prod['formato__capacidad'] > 0:
                unidad = 'L'          # Litros
            else:
                unidad = 'unidades'

            productos_data.append({
                'id': prod['id'],
                'nombre_comercial': prod['producto__nombre_comercial'],
                'costo': float(prod['producto__costo']) if prod['producto__costo'] else 0,
                'unidad_medida': unidad,
                'formato': prod.get('formato__unidad_medida', 'A Granel')
            })
    
        context = {
            'produccion_form': produccion_form,
            'materia_prima_form': materia_prima_form,
            'materias_primas_json': self.get_materias_primas_json(),
            'productos_data': productos_data,                     
            'produccion_base': self._obtener_produccion_base(request),
            'materias_primas_precargadas': datos_precargados.get('materias_primas_precargadas', []) if datos_precargados else [],
            'productos_precargados': datos_precargados.get('productos_precargados', []) if datos_precargados else [],  # <--- Clave corregida
        }
        return render(request, self.template_name, context)

    def _obtener_datos_precargados(self, request):
        """Extrae datos pre-cargados de query parameters o sesion"""
        datos = {}
    
        if 'produccion_base_id' in request.GET:
            try:
                produccion_base = Produccion.objects.get(id=request.GET.get('produccion_base_id'))
            
                datos = {
                    'produccion_base_id': str(produccion_base.id),
                    'produccion_base_lote': produccion_base.lote,
                    'planta_id': str(produccion_base.planta.id),
                    'catalogo_producto_id': str(produccion_base.catalogo_producto.id),
                    'cantidad_estimada': str(produccion_base.cantidad_estimada),
                    'prod_result': 'on' if produccion_base.prod_result else '',
                    'observaciones_reutilizacion': request.GET.get('referencia', f'Reutilizando {produccion_base.lote}'),
                
                    # Materias primas precargadas
                    'materias_primas_precargadas': self._obtener_materias_primas_precargadas(produccion_base),
                
                    # Productos precargados (NUEVO)
                    'productos_precargados': self._obtener_productos_precargados(produccion_base),
                }
            except Produccion.DoesNotExist:
                pass
    
        elif 'produccion_data' in request.session:
            session_data = request.session['produccion_data']
            if 'produccion_base_id' in session_data:
                datos.update(session_data)
    
        return datos

    def _obtener_productos_precargados(self, produccion_base):
        """Obtiene los productos consumidos en la producción base para precargar"""
        # Asegúrate de importar Prod_Inv_Producto
        from produccion.models import Prod_Inv_Producto
    
        productos = Prod_Inv_Producto.objects.filter(lote_prod=produccion_base)
        return [
            {
                'id': str(p.id),
                'producto_id': str(p.producto.id),
                'nombre': p.producto.nombre_comercial,
                'cantidad': str(p.cantidad_producto),
                'almacen_id': str(p.almacen.id),
                'almacen_nombre': p.almacen.nombre,
                'unidad_medida': 'unidades',  # Ajusta según la unidad real de tu producto
                'costo': str(p.producto.costo),
            }
            for p in productos
        ]

    def _obtener_materias_primas_precargadas(self, produccion_base):
        """Obtiene materias primas para pre-cargar"""
        materias = Prod_Inv_MP.objects.filter(lote_prod=produccion_base)
        return [
            {
                'id': str(mp.id),
                'materia_prima_id': str(mp.inv_materia_prima.id),
                'materia_prima_nombre': mp.inv_materia_prima.nombre,
                'cantidad': str(mp.cantidad_materia_prima),
                'almacen_id': str(mp.almacen.id),
                'almacen_nombre': mp.almacen.nombre,
                'unidad_medida': mp.inv_materia_prima.unidad_medida,
                'costo': str(mp.inv_materia_prima.costo),
            }
            for mp in materias
        ]

    def _obtener_produccion_base(self, request):
        """Obtiene la produccion base si existe"""
        produccion_base_id = None
        
        if 'produccion_base_id' in request.GET:
            produccion_base_id = request.GET.get('produccion_base_id')
        elif 'produccion_data' in request.session and 'produccion_base_id' in request.session['produccion_data']:
            produccion_base_id = request.session['produccion_data']['produccion_base_id']
        
        if produccion_base_id:
            try:
                return Produccion.objects.get(id=produccion_base_id)
            except Produccion.DoesNotExist:
                return None
        return None
    
    def post(self, request):
        costo_mp = 0
        step = request.POST.get('step')
        
        if step == '1':
            return self.procesar_paso_1(request)        
        elif step == '2':
            return self.procesar_paso_2(request)
        else:
            return JsonResponse({'success': False, 'errors': 'Paso no valido'})
    
    def procesar_paso_1(self, request):
        """Guardar solo los valores primitivos en sesion"""
        produccion_form = ProduccionForm(request.POST)
        if produccion_form.is_valid():
            # Procesar producto (existente o nuevo)
            """catalogo_producto_id = self.procesar_producto(request)
            if not catalogo_producto_id:
                return JsonResponse({
                    'success': False, 
                    'errors': 'Error al procesar el producto'
                })
            
            # Extraer solo datos primitivos para la sesión
            session_data = {
                'catalogo_producto_id': str(catalogo_producto_id),  # Guardar como string
                'cantidad_estimada': request.POST.get('cantidad_estimada'),
                'prod_result': request.POST.get('prod_result'),
                'planta_id': request.POST.get('planta'),  # Guardar el ID como string
            }"""
            # Guardar en sesión, NO en base de datos
            catalogo_producto_id = self.procesar_producto_en_sesion(request)
        
            session_data = {
                'catalogo_producto_id': str(catalogo_producto_id) if catalogo_producto_id else None,
                'cantidad_estimada': request.POST.get('cantidad_estimada'),
                'prod_result': request.POST.get('prod_result'),
                'planta_id': request.POST.get('planta'),
                'nuevo_producto_nombre': request.POST.get('nuevo_producto_nombre'),  # Guardar nombre
                'producto_creado': False  # Bandera para saber si ya se creó
            }
                    
            # Guardar en sesión
            request.session['produccion_data'].update(session_data)
            request.session.modified = True
            return JsonResponse({'success': True, 'step': 2})
        else:
            return JsonResponse({'success': False, 'errors': produccion_form.errors})

    def procesar_producto_en_sesion(self, request):
        """Similar a procesar_producto pero sin guardar en BD"""
        nuevo_producto_nombre = request.POST.get('nuevo_producto_nombre')
        catalogo_producto_id = request.POST.get('catalogo_producto')
    
        if nuevo_producto_nombre:
            # NO crear en BD, solo devolver el nombre para guardar en sesión
            return None  # Indicar que es un producto nuevo aún no creado
        elif catalogo_producto_id:
            return catalogo_producto_id
        return None

    def procesar_producto(self, request):
        """Procesa el producto (existente o nuevo) y retorna el ID"""
        nuevo_producto_nombre = request.POST.get('nuevo_producto_nombre')
        catalogo_producto_id = request.POST.get('catalogo_producto')
        prod_base = request.POST.get('prod_result')

        if nuevo_producto_nombre:
            # Crear nuevo producto en el catálogo
            try:
                #formato_agranel = Formato.objects.filter(capacidad=0).first()
                if prod_base == None:
                    val_prod_base = False
                else:
                    val_prod_base = True
                # Crear en CatalogoProducto (no en Producto)
                catalogo_producto = Producto.objects.create( 
                                nombre_comercial=nuevo_producto_nombre.strip(), 
                                #formato=formato_agranel, 
                                #estado="produccion",
                                prod_base=val_prod_base,
                                costo=0
                                )
                return catalogo_producto.id
                
            except Exception as e:
                print(f"Error al crear producto: {e}")
                return None
        elif catalogo_producto_id:
            # Usar producto existente - verificar que existe
            try:
                catalogo_producto = Producto.objects.filter(id=catalogo_producto_id).first()
                if not catalogo_producto:
                    catalogo_producto = MateriaPrima.objects.filter(id=catalogo_producto_id).first()
                return catalogo_producto_id
            except Exception as e:
                print(f"Producto con ID {catalogo_producto_id} no existe: {e}")
                return None
        else:
            print("No esta el producto ni producto existente")
            return None

    def procesar_paso_2(self, request):
        try:
            print("=== INICIO PROCESAR PASO 2 ===")
            produccion_data = request.session.get('produccion_data', {})
                
            # VERIFICAR SI ES PRODUCTO NUEVO Y CREARLO AHORA
            catalogo_producto_id = produccion_data.get('catalogo_producto_id')
            nuevo_producto_nombre = produccion_data.get('nuevo_producto_nombre')
        
            if not catalogo_producto_id and nuevo_producto_nombre:
                # Crear el producto AHORA, en el paso 2
                try:
                    catalogo_producto = Producto.objects.create(
                        nombre_comercial=nuevo_producto_nombre.strip(),
                        prod_base=produccion_data.get('prod_result') == 'on',
                        costo=0
                    )
                    catalogo_producto_id = catalogo_producto.id
                    # Actualizar sesión con el ID creado
                    produccion_data['catalogo_producto_id'] = str(catalogo_producto_id)
                    produccion_data['producto_creado'] = True
                    request.session.modified = True
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'errors': f'Error al crear el producto: {str(e)}'
                    })
    
            # Procesar materias primas
            try:
                materias_primas = self.procesar_materias_primas(request.POST)
                productos = self.procesar_productos(request.POST)
                
            except ValueError as e:
                # Si hay error y se creó un producto nuevo, ELIMINARLO
                if produccion_data.get('producto_creado') and catalogo_producto_id:
                    try:
                        Producto.objects.filter(id=catalogo_producto_id).delete()
                        produccion_data['catalogo_producto_id'] = None
                        produccion_data['producto_creado'] = False
                        request.session.modified = True
                    except:
                        pass
                return JsonResponse({'success': False, 'errors': str(e)})
        
            # Calcular costo total
            costo_total = Decimal('0')
            for mp in materias_primas:
                costo_total += mp['costo']
            for prod in productos:
                costo_total += prod['costo']

            try:
                # Obtener la instancia de Planta
                planta_id = normalizar_UUID(produccion_data['planta_id'])
                planta_instance = Planta.objects.get(id=planta_id)
                #produccion_data['catalogo_producto_id']
                catalogo_producto_instance = Producto.objects.filter(id=catalogo_producto_id).first()
            
                if not catalogo_producto_instance:
                    raise ValueError("No se encontró el producto especificado")
            
                # GENERAR LOTE CON EL NUEVO FORMATO
                cantidad_estimada = float(produccion_data['cantidad_estimada'])
                lote_generado = Produccion.generar_lote(
                    catalogo_producto=catalogo_producto_instance,
                    planta=planta_instance,
                    cantidad_estimada=cantidad_estimada
                )
        
                if produccion_data.get('prod_result'): 
                    product = True
                else:
                    product = False

                # Verificar que el lote no exista (por si acaso)
                intentos = 0
                lote_final = lote_generado
        
                while Produccion.objects.filter(lote=lote_final).exists() and intentos < 10:
                    intentos += 1
                    # Si por alguna rareza existe, añadir un sufijo
                    lote_final = f"{lote_generado}-{intentos:02d}"
        
                # Obtener producción base si existe
                produccion_base = None
                if produccion_data.get('produccion_base_id'):
                    produccion_base = Produccion.objects.get(id=produccion_data['produccion_base_id'])
                else:
                    print("No hay produccion base")

                # Guardar producción
                produccion = Produccion.objects.create(
                    lote=lote_final,
                    catalogo_producto=catalogo_producto_instance,
                    prod_result=product,
                    cantidad_estimada=Decimal(produccion_data['cantidad_estimada']),
                    costo=costo_total,
                    planta=planta_instance,
                    estado='Planificada',
                    produccion_base=produccion_base,
                    observaciones_reutilizacion=produccion_data.get('observaciones_reutilizacion', '')
                )
                
                # --- Crear vale para materias primas ---
                vale_mp = None

                if materias_primas:
                    id_almacen = materias_primas[0]['almacen']
                    almacen_obj = Almacen.objects.get(id=id_almacen)
                    if not vale_mp:
                        vale_mp = Vale_Movimiento_Almacen.objects.create(
                            tipo='Solicitud',
                            entrada=False,
                            almacen=almacen_obj,
                            origen='Producción en ' + planta_instance.nombre,
                            destino=almacen_obj.nombre,
                            lote_No=produccion.lote,
                            estado='confirmado',
                            despachado_por=request.user.first_name
                        )
    
                    for mp_data in materias_primas:
                        try:
                            almacen_o = Almacen.objects.get(id=mp_data['almacen'])
                            # Usar el objeto que ya tenemos en mp_data
                            inv_materia_prima_obj = mp_data.get('inv_materia_prima_obj')
                            if not inv_materia_prima_obj:
                                # Si no vino en mp_data, buscarlo
                                inv_materia_prima_obj = Inv_Mat_Prima.objects.get(id=mp_data['inv_materia_prima_id'])
                            inv_materia_prima_obj = Inv_Mat_Prima.objects.get(id=inv_materia_prima_obj.id)
                            produccion.refresh_from_db()  # Recarga el objeto desde la BD
                            vale_mp.full_clean()
                            
                            # Si alguna no existe, lanzar un error descriptivo
                            if not Produccion.objects.filter(id=produccion.id).exists():
                                raise ValueError("La producción no se guardó correctamente en BD")
                            if not Inv_Mat_Prima.objects.filter(id=inv_materia_prima_obj.id).exists():
                                raise ValueError(f"Inv_Mat_Prima con ID {inv_materia_prima_obj.id} no existe en BD")
                            if not Almacen.objects.filter(id=almacen_o.id).exists():
                                raise ValueError(f"Almacén con ID {almacen_o.id} no existe")
                            if not Vale_Movimiento_Almacen.objects.filter(id=vale_mp.id).exists():
                                raise ValueError(f"Vale con ID {vale_mp.id} no existe")
                
                            prod_inv= Prod_Inv_MP.objects.create(
                                lote_prod=produccion,
                                inv_materia_prima=inv_materia_prima_obj,
                                cantidad_materia_prima=mp_data['cantidad'],
                                almacen=almacen_o,
                                vale=vale_mp
                            )
            
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            raise ValueError(f"Error al crear Prod_Inv_MP: {str(e)}")
            
                # --- Crear vale para productos ---
                vale_prod = None
                if productos:
                    id_almacen = normalizar_UUID(productos[0]['almacen']) 
                    almacen_obj = Almacen.objects.get(id=id_almacen)
                    if not vale_prod:
                        vale_prod = Vale_Movimiento_Almacen.objects.create(
                            tipo='Solicitud',
                            entrada=False,
                            almacen=almacen_obj,
                            origen='Producción en ' + planta_instance.nombre,
                            destino=almacen_obj.nombre,
                            lote_No=produccion.lote,
                            estado='confirmado',    
                            despachado_por=request.user.first_name
                        )

                    try:
                        for prod_data in productos:
                            almacen_o_id = normalizar_UUID(prod_data['almacen'])
                            almacen_o = Almacen.objects.get(id=almacen_o_id)
                    
                            inv_prod_obj_id = normalizar_UUID(prod_data['inv_producto_id'])
                            producto_obj2 = Inv_Producto.objects.get(id=inv_prod_obj_id)
                            Prod_Inv_Producto.objects.create(
                                producto=producto_obj2,
                                cantidad_producto=prod_data['cantidad'],
                                almacen=almacen_o,
                                vale=vale_prod,
                                lote_prod=produccion
                            )
                    except(ValueError) as e:
                        print(f"Error detallado {e}")

                # Limpiar sesión
                if 'produccion_data' in request.session:
                    del request.session['produccion_data']
                    request.session.modified = True

                # Mensaje específico para reutilización
                if produccion.produccion_base:
                    message = f'Producción creada reutilizando {produccion_base.lote} como base'
                else:
                    message = 'Producción creada exitosamente'
        
                return JsonResponse({
                    'success': True, 
                    'message': message, 
                    'produccion_id': produccion.id,
                    'redirect_url': reverse('produccion_list')
                })
        
            except ValueError as e:
                raise ValueError(str(e))
            except Exception as e:
                return JsonResponse({'success': False, 'errors': f'Error al guardar: {str(e)}'})

        except Exception as e:
            # Capturar el error y enviarlo como JSON válido
            import traceback
            error_detallado = traceback.format_exc()
            print(f"ERROR DETALLADO:\n{error_detallado}")
        
            # Devolver JSON válido
            return JsonResponse({
                'success': False, 
                'errors': f'Error: {str(e)}'
            }, status=400)  # Usar status 400 para errores de cliente

    def get_materias_primas_json(self):
        materias_primas = MateriaPrima.objects.all().values(
            'id', 'nombre', 'tipo_materia_prima', 'conformacion', 'unidad_medida', 'concentracion', 'costo'
        )
    
    def procesar_materias_primas(self, post_data):
        materias_primas = []
     
        if not post_data:
            return []
    
        i = 0
    
        def get_value(data, key):
            if isinstance(data, dict):
                return data.get(key)
            elif hasattr(data, 'get'):
                return data.get(key)
            return None

        while True:
            materia_prima_key = f'materias_primas[{i}][materia_prima]'
            materia_prima_id = get_value(post_data, materia_prima_key)
        
            if not materia_prima_id:
                break
                
            materia_prima_id = normalizar_UUID(materia_prima_id)    
            cantidad_str = get_value(post_data, f'materias_primas[{i}][cantidad]')
        
            if not all([materia_prima_id, cantidad_str]):
                i += 1
                continue
        
            try:
                cantidad = Decimal(str(cantidad_str))
            
                try:
                    # Primero intentar búsqueda directa
                    inv_materia_prima_obj = Inv_Mat_Prima.objects.get(id=materia_prima_id)
                    
                except (Inv_Mat_Prima.DoesNotExist, ValueError) as e:
                    # Si tiene formato "ID - Nombre", extraer solo el ID
                    if isinstance(materia_prima_id, str) and ' - ' in materia_prima_id:
                        id_limpio = materia_prima_id.split(' - ')[0]
                        inv_materia_prima_obj = Inv_Mat_Prima.objects.get(id=id_limpio)
                    else:
                        raise
            
                almacen_obj = inv_materia_prima_obj.almacen
            
                # Verificar inventario
                if cantidad > inv_materia_prima_obj.cantidad:
                    nombre_mp = inv_materia_prima_obj.materia_prima.nombre
                    cantidad_disponible = inv_materia_prima_obj.cantidad
                    unidad = inv_materia_prima_obj.materia_prima.unidad_medida
                
                    error_msg = (f"Cantidad insuficiente de '{nombre_mp}'. "
                       f"Requerido: {cantidad} {unidad}, "
                       f"Disponible: {cantidad_disponible} {unidad}")
                
                    raise ValueError(error_msg)
        
                # Calcular costo
                costo_mp = Decimal(str(inv_materia_prima_obj.materia_prima.costo)) * cantidad
        
                materias_primas.append({
                    'materia_prima': inv_materia_prima_obj.materia_prima.id,
                    'inv_materia_prima_id': inv_materia_prima_obj.id,  # Guardar ambos
                    'cantidad': cantidad,
                    'almacen': almacen_obj.id,
                    'costo': costo_mp,
                    'materia_prima_obj': inv_materia_prima_obj.materia_prima,
                    'inv_materia_prima_obj': inv_materia_prima_obj,
                    'almacen_obj': almacen_obj
                })
            
            except Inv_Mat_Prima.DoesNotExist as e:
                raise ValueError(f"Materia prima con ID '{materia_prima_id}' no existe en inventario")
            except ValueError as e:
                print(f"Error de validación MP {i}: {e}")
                raise
            except Exception as e:
                print(f"Error inesperado MP {i}: {e}")
                raise
        
            i += 1
    
        return materias_primas

    def procesar_productos(self, post_data):
        productos = []

        if not post_data:
            return []
        
        i = 0

        def get_value(data, key):
            if isinstance(data, dict):
                return data.get(key)
            return data.get(key) if hasattr(data, 'get') else None

        while True:
            producto_key = f'productos[{i}][producto]'
            producto_id = get_value(post_data, producto_key)
            
            if not producto_id:
                break
            
            producto_id = normalizar_UUID(producto_id)
            cantidad_str = get_value(post_data, f'productos[{i}][cantidad]')
            
            if not all([producto_id, cantidad_str]):
                i += 1
                continue

            try:
                cantidad = Decimal(cantidad_str)

                try:
                    inv_producto_obj = Inv_Producto.objects.get(id=producto_id)
                    
                except (Inv_Producto.DoesNotExist, ValueError) as e:
                    
                    # Si tiene formato "ID - Nombre", extraer solo el ID
                    if isinstance(producto_id, str) and ' - ' in producto_id:
                        id_limpio = producto_id.split(' - ')[0]
                        inv_producto_obj = Inv_Producto.objects.get(id=id_limpio)
                    else:
                        raise

                almacen_obj = inv_producto_obj.almacen
            
                # Verificar disponibilidad
                if cantidad > inv_producto_obj.cantidad:
                    nombre_prod = inv_producto_obj.producto.nombre_comercial
                    cantidad_disponible = inv_producto_obj.cantidad
                    error_msg = (f"Cantidad insuficiente de '{nombre_prod}'. "
                       f"Requerido: {cantidad}, "
                       f"Disponible: {cantidad_disponible}")
                    raise ValueError(error_msg)

                costo_total = Decimal(str(inv_producto_obj.producto.costo)) * cantidad
                inv_producto_obj_id=normalizar_UUID(inv_producto_obj.id)
                prod_obj_id = normalizar_UUID(inv_producto_obj.producto.id)
                almacen_obj_id = normalizar_UUID(almacen_obj.id)
                
                productos.append({
                    'producto': prod_obj_id,
                    'inv_producto_id': inv_producto_obj_id,  # Guardar el ID del inventario
                    'cantidad': cantidad,
                    'almacen': almacen_obj_id,
                    'costo': costo_total,
                    'producto_obj': inv_producto_obj.producto,
                    'almacen_obj': almacen_obj,
                    'inv_producto_obj': inv_producto_obj
                })
            
            except Inv_Producto.DoesNotExist as e:
                raise ValueError(f"Producto con ID '{producto_id}' no existe en inventario")
            except ValueError as e:
                print(f"Error de validacin producto {i}: {e}")
                raise
            except Exception as e:
                print(f"Error inesperado producto {i}: {e}")
                raise
            
            i += 1

        return productos

class ProduccionDetailView(LoginRequiredMixin, DetailView):
    model = Produccion
    template_name = 'produccion/detalle_produccion.html'
    context_object_name = 'produccion'
    pk_url_kwarg = 'pk'  # Si usas 'id' en la URL en lugar de 'pk'
    
    def get_object(self, queryset=None):
        """Obtener el objeto o retornar 404"""
        return get_object_or_404(Produccion, id=self.kwargs.get('pk'))
    
    def get_context_data(self, **kwargs):
        """Agregar datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        produccion = self.object
        
        # 1. Materias primas utilizadas
        materias_primas = Prod_Inv_MP.objects.filter(lote_prod=produccion).select_related(
            'inv_materia_prima', 'almacen'
        )

        prod_ins = Prod_Inv_Producto.objects.filter(lote_prod=produccion).select_related(
            'producto', 'almacen'
        )

        vales_asociados = Vale_Movimiento_Almacen.objects.filter(
            lote_No=produccion.lote  # Si tienes este campo
        ).order_by('-fecha_creacion')

        vales_ids = list(vales_asociados.values_list('consecutivo', flat=True))
        ids = []
        for id in vales_ids:
            ids.append(str(id))

         # Obtener todos los movimientos de cada tipo
        movimientos_mp = Movimiento_MP.objects.filter(
            vale__in=vales_asociados
        ).select_related('materia_prima', 'materia_prima__materia_prima', 'vale', 'vale__almacen')
        
        movimientos_prod = Movimiento_Prod.objects.filter(
            vale__in=vales_asociados
        ).select_related('producto', 'producto__producto', 'vale', 'vale__almacen')
        
        movimientos_ins = Movimiento_Ins.objects.filter(
            vale__in=vales_asociados
        ).select_related('insumo', 'vale', 'vale__almacen')
        
        movimientos_ee = Movimiento_EE.objects.filter(
            vale__in=vales_asociados
        ).select_related('envase_embalaje', 'vale', 'vale__almacen')
        
        # 2. Calcular total de costos de materias primas
        costo_total_mp = produccion.costo_total_materias_primas
        costo_total_prod = produccion.costo_total_prod_ins
        
        # 3. Pruebas químicas asociadas
        pruebas_quimicas = produccion.pruebas_quimicas.all()  # Usando related_name
        
        # 4. Historial de cambios (si tienes model History)
        try:
            from django.contrib.admin.models import LogEntry
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(produccion)
            historial = LogEntry.objects.filter(
                object_id=produccion.id,
                content_type=content_type
            ).order_by('-action_time')
        except:
            historial = []

        estado_actual = produccion.estado
        
        if estado_actual == 'Planificada':
            porcentaje_avance = 5
        elif estado_actual == 'En proceso: Iniciando mezcla':
            porcentaje_avance = 10
        elif estado_actual == 'En proceso: Agitado':
            porcentaje_avance = 40
        elif estado_actual == 'En proceso: Validación':
            porcentaje_avance = 80
        else:
            porcentaje_avance = 100

        # Calcular costo por litro
        if not produccion.cantidad_real:
            if produccion.cantidad_estimada:
                costo_litro = produccion.costo / float(produccion.cantidad_estimada)
            else:
                costo_litro = 0
        else:
            costo_litro = produccion.costo / float(produccion.cantidad_real)
             
        print(f'ids: {ids}')
        # 5. Datos para gráficos o estadísticas
        datos_produccion = {
            'lote_base': produccion.produccion_base.lote if produccion.produccion_base else '',
            'costo_materias_primas': costo_total_mp,
            'costo_prod_ins': costo_total_prod,
            'costo_total': produccion.costo,
            'diferencia_costo': produccion.costo - float(costo_total_mp+costo_total_prod),
            'eficiencia': (produccion.cantidad_real or 0) / produccion.cantidad_estimada * 100 
            if produccion.cantidad_real else 0,
            'porcentaje_avance': porcentaje_avance,
            'costo_litro': costo_litro,
            # Agregar resumen de movimientos
            'vales_asociados': vales_asociados,
            'total_movimientos_mp': movimientos_mp.count(),
            'total_movimientos_prod': movimientos_prod.count(),
            'total_movimientos_ins': movimientos_ins.count(),
            'total_movimientos_ee': movimientos_ee.count(),
        }

        # 6. Productos relacionados (si aplica)
        producto_relacionado = produccion.catalogo_producto
        
        context.update({
            'materias_primas': materias_primas,
            'prod_ins':prod_ins,
            'costo_total_mp': costo_total_mp,
            'costo_total_prod':costo_total_prod,
            'pruebas_quimicas': pruebas_quimicas,
            'historial': historial,
            'datos_produccion': datos_produccion,
            'producto_relacionado': producto_relacionado,
            'estados_disponibles': self.get_estados_disponibles(produccion),
            'puede_editar': self.puede_editar_produccion(produccion),
            # Movimientos de inventario
            'movimientos_mp': movimientos_mp,
            'movimientos_prod': movimientos_prod,
            'movimientos_ins': movimientos_ins,
            'movimientos_ee': movimientos_ee,
            'vales_asociados': vales_asociados,
            'vales_ids': ids, 
        })
        
        return context
    
    def get_estados_disponibles(self, produccion):
        """Retorna los estados a los que puede cambiar la producción"""
        estados = []
        estado_actual = produccion.estado
        
        if estado_actual == 'Planificada':
            estados = ['En proceso: Iniciando mezcla', 'Cancelada']
        elif estado_actual == 'En proceso: Iniciando mezcla':
            estados = ['En proceso: Agitado']
        elif estado_actual == 'En proceso: Agitado':
            estados = ['En proceso: Validación']
        elif estado_actual == 'En proceso: Validación':
            estados = ['Concluida-Satisfactoria', 'Concluida-Rechazada']
        
        return estados
    
    def puede_editar_produccion(self, produccion):
        """Determina si el usuario puede editar esta producción"""
        estados_editables = ['Planificada', 'En proceso: Iniciando mezcla']
        return produccion.estado in estados_editables and self.request.user.has_perm('app.change_produccion')

@login_required
def reutilizar_produccion(request, pk):
    """
    Redirige a crear nueva producción con datos de la producción base
    """
    produccion_base = get_object_or_404(Produccion, id=pk)
    
    if not produccion_base.puede_ser_reutilizada:
        messages.error(request, 'Esta producción no puede ser reutilizada')
        return redirect('produccion_detail', id=pk)
    
    # Crear datos para pre-cargar en la nueva producción
    datos_precargados = {
        'produccion_base_id': str(produccion_base.id),
        'referencia': f"Reutilizando {produccion_base.lote}",
        
        # Pre-cargar datos de la producción base
        'planta_id': str(produccion_base.planta.id),
        'prod_result': 'on' if produccion_base.prod_result else '',
        
        # Materias primas para pre-cargar (opcional)
        'materias_primas_precargadas': _obtener_materias_primas_precargadas(produccion_base)
    }
    produccion_base.estado = 'Concluida-Rechazada-R'
    produccion_base.save()
    # Codificar datos en query string
    query_string = urllib.parse.urlencode(datos_precargados)
    
    # Redirigir a crear producción con datos pre-cargados
    url = f"{reverse('crear_produccion')}?{query_string}"
    return redirect(url)

@login_required
def _obtener_materias_primas_precargadas(produccion_base):
    """Obtiene las materias primas para pre-cargar en el formulario"""
    materias = Prod_Inv_MP.objects.filter(lote_prod=produccion_base)
    return [
        {
            'materia_prima_id': str(mp.inv_materia_prima.id),
            'cantidad': str(mp.cantidad_materia_prima),
            'almacen_id': str(mp.almacen.id),
        }
        for mp in materias
    ]

@login_required
def get_materias_primas_data(request):
    """API para obtener datos de materias primas en JSON"""
    materias_primas = MateriaPrima.objects.all().values(
        'id', 'nombre', 'tipo', 'conformacion', 'unidad_medida', 'concentracion', 'costo'
    )
    return JsonResponse(list(materias_primas), safe=False)

#Flujo básico de la producción
@login_required
def iniciar_produccion(request, pk):
    """View para iniciar una producción específica"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    mp = Prod_Inv_MP.objects.filter(lote_prod=produccion)
    prod = Prod_Inv_Producto.objects.filter(lote_prod=produccion)

    if mp and mp[0].vale.estado == 'confirmado' or prod and prod[0].vale.estado == 'confirmado':
        messages.warning(request, f' Aun no se ha sacado del almacén las materias primas solicitadas')
        return redirect('produccion_list')

    if produccion.estado == 'Planificada':
        produccion.estado = 'En proceso: Iniciando mezcla'
        produccion.save()
        messages.success(request, f'Producción {produccion.lote} iniciada correctamente')
    else:
        messages.warning(request, f'La producción {produccion.lote} ya está en estado: {produccion.estado}')
    
    return redirect('produccion_list')

@login_required
def agita_produccion(request, pk):
    produccion_p = get_object_or_404(Produccion, pk=pk)
        
    if produccion_p.estado == 'En proceso: Iniciando mezcla':
        produccion_p.estado = 'En proceso: Agitado'
        produccion_p.save()
        messages.success(request, f'Producción {produccion_p.lote} actualizada correctamente')
    else:
        messages.warning(request, f'La producción {produccion_p.lote} ya está en estado: {produccion_p.estado}')
    
    return redirect('produccion_list')

@login_required
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
                    produccion.fecha_actualizacion = datetime.now()
                    produccion.save()

                    messages.success(request, f'Producción {produccion.lote} completada. Cantidad obtenida: {cantidad_real}')
                    return redirect('produccion_list')
                else:
                    messages.error(request, 'La cantidad real debe ser mayor a 0')
            except ValueError:
                messages.error(request, 'La cantidad debe ser un número válido')
        else:
            messages.error(request, 'Debe especificar la cantidad obtenida')
    
    return render(request, 'produccion/concluir_produccion.html', { 'produccion': produccion })

@login_required
def cancelar_produccion(request, pk):
    """View para cancelar una producción con observaciones"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    # Verificar si puede ser cancelada
    if not produccion.puede_ser_cancelada():
        messages.error(request, f'No se puede cancelar la producción {produccion.lote} porque ya está {produccion.get_estado_display().lower()}')
        return redirect('produccion_list')
    
    if request.method == 'POST':
        form = CancelarProduccionForm(request.POST, produccion=produccion)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Producción {produccion.lote} cancelada correctamente')
            
            # Notificar a admin, verificar si las materias primas ya salieron de almacen
            target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
            vale_salida = Vale_Movimiento_Almacen.objects.filter(lote_No = produccion.lote)
            # Crear notificaciones para cada usuario en ese grupo
            for group in target_groups:
                for user in group.customuser_set.all():
                    # Notificación en base de datos
                    Notification.objects.create(
                        user=user,
                        message=f"Cancelación de la producción: {produccion.lote}.",
                        link=f'/produccion/'  # ¡.  
                    )
                    
            for vale in vale_salida:
                if vale.estado == 'confirmado':
                    vale.estado = 'cancelado'
                elif vale.estado == 'despachado':
                    vale_d = Vale_Movimiento_Almacen.objects.create(
                                    tipo='Devolución',
                                    destino=vale.almacen.nombre,
                                    origen=produccion.planta.nombre,
                                    entrada=False,
                                    almacen=vale.almacen,
                                    lote_No = produccion.lote,
                                    estado='confirmado',
                                    descripcion=f'Devolución de vale {vale.consecutivo} por cancelación de producción {produccion.lote}',
                                    despachado_por=request.user.first_name
                                )
                    materias_primas = Prod_Inv_MP.objects.filter(vale=vale)
                    for mp in materias_primas:
                        Movimiento_MP.objects.create(
                                materia_prima=mp.inv_materia_prima,
                                cantidad=mp.cantidad_materia_prima,
                                vale=vale_d
                            )
                vale.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Producción cancelada correctamente',
                    'nuevo_estado': produccion.estado
                })
            
            return redirect('produccion_list')
        else:
            messages.error(request, 'Error al cancelar la producción')
    else:
        form = CancelarProduccionForm(produccion=produccion)
    
    return render(request, 'produccion/cancelar_produccion.html', {
        'produccion': produccion,
        'form': form
    })

# View para ver detalles de cancelación
@login_required
def detalle_cancelacion(request, pk):
    """View para ver los detalles de una producción cancelada"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if produccion.estado != 'Cancelada':
        messages.warning(request, 'Esta producción no está cancelada')
        return redirect('produccion_list')
    
    return render(request, 'produccion/detalle_cancelacion.html', {
        'produccion': produccion
    })

class EditarProduccionView(LoginRequiredMixin, View):
    template_name = 'produccion/editar_produccion.html'
    
    def get(self, request, pk):
        # Obtener la producción existente
        produccion = get_object_or_404(Produccion, id=pk)
    
        # Inicializar sesión con los datos actuales
        request.session['editar_produccion_data'] = {
            'produccion_id': str(produccion.id),
            'catalogo_producto_id': str(produccion.catalogo_producto.id),
            'cantidad_estimada': str(produccion.cantidad_estimada),
            'planta_id': str(produccion.planta.id),
            'prod_result': 'on' if produccion.prod_result else '',
        }
    
        # Obtener materias primas actuales
        materias_primas_actuales = Prod_Inv_MP.objects.filter(lote_prod=produccion)
        materias_primas_json = self._obtener_materias_primas_json(materias_primas_actuales)

        # Obtener productos base actuales   
        productos_prod_actuales = Prod_Inv_Producto.objects.filter(lote_prod=produccion)
        productos_prod_json = self._obtener_productos_prod_json(productos_prod_actuales)             
    
        # Obtener materias primas disponibles
        materias_disponibles = Inv_Mat_Prima.objects.select_related('materia_prima', 'almacen').filter(
            cantidad__gt=0,
        )
    
        materias_disponibles_list = []
        for inv in materias_disponibles:
            materias_disponibles_list.append({
                'id': str(inv.id),
                'materia_prima_id': str(inv.materia_prima.id),
                'materia_prima_nombre': inv.materia_prima.nombre,
                'unidad_medida': inv.materia_prima.unidad_medida,
                'costo': float(inv.materia_prima.costo),
                'almacen_id': str(inv.almacen.id),
                'almacen_nombre': inv.almacen.nombre,
                'cantidad_disponible': float(inv.cantidad)
            })

        # Obtener productos disponibles (como insumo) - CORREGIDO
        inv_productos = Inv_Producto.objects.select_related('producto', 'formato', 'almacen').filter(
            cantidad__gt=0, formato__capacidad = 0
        )
        
        productos_disponibles_list = []
        for inv in inv_productos:
            productos_disponibles_list.append({
                'id': str(inv.id),
                'producto_id': str(inv.producto.id),
                'nombre': inv.producto.nombre_comercial,
                'unidad_medida': inv.formato.unidad_medida if inv.formato else 'unidades',
                'costo': float(inv.producto.costo),
                'almacen_id': str(inv.almacen.id),
                'almacen_nombre': inv.almacen.nombre,
                'cantidad_disponible': float(inv.cantidad),
            })
    
        # Obtener almacenes
        almacenes = Almacen.objects.all()  
        almacenes_list = [{'id': str(a.id), 'nombre': a.nombre} for a in almacenes]
    
        context = {
            'produccion': produccion,
            'materias_primas_json': json.dumps(materias_primas_json),
            'productos_prod_json': json.dumps(productos_prod_json),
            'materias_disponibles_json': json.dumps(materias_disponibles_list),
            'productos_disponibles_json': json.dumps(productos_disponibles_list),
            'almacenes_json': json.dumps(almacenes_list),
        }
    
        return render(request, self.template_name, context)

    def _obtener_materias_primas_json(self, materias_primas_actuales):
        """Convierte las materias primas actuales a JSON para el frontend"""
        materias = []
        for mp in materias_primas_actuales:
            inventario = Inv_Mat_Prima.objects.filter(
                materia_prima=mp.inv_materia_prima.materia_prima,
                almacen=mp.almacen
            ).first()
        
            materia_data = {
                'id': str(mp.id),
                'inventario_id': str(mp.inv_materia_prima.id) if mp.inv_materia_prima else None,
                'materia_prima_id': str(mp.inv_materia_prima.materia_prima.id),
                'materia_prima_nombre': mp.inv_materia_prima.materia_prima.nombre,
                'cantidad': float(mp.cantidad_materia_prima),
                'almacen_id': str(mp.almacen.id),
                'almacen_nombre': mp.almacen.nombre,
                'unidad_medida': mp.inv_materia_prima.materia_prima.unidad_medida,
                'costo_unitario': float(mp.inv_materia_prima.materia_prima.costo),
                'costo_total': float(mp.cantidad_materia_prima) * float(mp.inv_materia_prima.materia_prima.costo),
                'inventario_disponible': float(inventario.cantidad) if inventario else 0,
            }
            materias.append(materia_data)
        return materias

    def _obtener_productos_prod_json(self, productos_prod_actuales):
        """Convierte los productos actuales a JSON para el frontend"""
        productos = []
        for pp in productos_prod_actuales:
            inventario = pp.producto
            """ inventario = Inv_Producto.objects.filter(
                producto=pp.producto.producto,
                formato=pp.producto.formato,
                almacen=pp.almacen
            ).first() """
        
            producto_data = {
                'id': str(pp.id),
                'inventario_id': str(pp.producto.id) if pp.producto else None,
                'producto_id': str(pp.producto.producto.id),
                'formato': str(pp.producto.formato),
                'nombre': pp.producto.producto.nombre_comercial,
                'cantidad': float(pp.cantidad_producto),
                'almacen_id': str(pp.almacen.id),
                'almacen_nombre': pp.almacen.nombre,
                'unidad_medida': pp.producto.formato.unidad_medida if pp.producto.formato else 'unidades',
                'costo_unitario': float(pp.producto.producto.costo),
                'costo_total': float(pp.cantidad_producto) * float(pp.producto.producto.costo),
                'inventario_disponible': float(inventario.cantidad) if inventario else 0,
            }
            productos.append(producto_data)
        print(f'productos de la produccion: {productos}')
        return productos
    
    def post(self, request, pk):
        produccion = get_object_or_404(Produccion, id=pk)
        step = request.POST.get('step')
        
        if step == '1':
            return self.procesar_paso_1(request, produccion)
        elif step == '2':
            return self.procesar_paso_2(request, produccion)
        else:
            return JsonResponse({'success': False, 'errors': 'Paso no válido'})
    
    def procesar_paso_1(self, request, produccion):
        cantidad_estimada = request.POST.get('cantidad_estimada')
        if not cantidad_estimada:
            return JsonResponse({'success': False, 'errors': 'La cantidad estimada es obligatoria'})
        try:
            cantidad_decimal = Decimal(cantidad_estimada)
            if cantidad_decimal <= 0:
                return JsonResponse({'success': False, 'errors': 'La cantidad debe ser mayor a cero'})
            
            editar_data = request.session.get('editar_produccion_data', {})
            editar_data['cantidad_estimada'] = str(cantidad_decimal)
            request.session['editar_produccion_data'] = editar_data
            request.session.modified = True
        
            return JsonResponse({'success': True, 'step': 2})
        except (ValueError, InvalidOperation) as e:
            return JsonResponse({'success': False, 'errors': f'La cantidad no es válida: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': f'Error: {str(e)}'})
    
    def procesar_paso_2(self, request, produccion):
        """Actualizar materias primas y productos"""
        try:
            materias_primas_nuevas = self.procesar_materias_primas(request.POST)
            productos_nuevos = self.procesar_productos(request.POST)  # ✅ Descomentar
        except ValueError as e:
            return JsonResponse({'success': False, 'errors': str(e)})

        try:
            with transaction.atomic():
                # 1. Actualizar cantidad estimada
                editar_data = request.session.get('editar_produccion_data', {})
                if 'cantidad_estimada' in editar_data:
                    produccion.cantidad_estimada = Decimal(editar_data['cantidad_estimada'])
                
                # 2. Calcular nuevo costo total
                costo_total = sum(Decimal(str(mp['costo'])) for mp in materias_primas_nuevas) + \
                              sum(Decimal(str(prod['costo'])) for prod in productos_nuevos)
                produccion.costo = costo_total
                
                # 3. Obtener registros actuales
                materias_actuales = Prod_Inv_MP.objects.filter(lote_prod=produccion)
                productos_actuales = Prod_Inv_Producto.objects.filter(lote_prod=produccion)
                
                # 4. Identificar IDs que se mantienen
                ids_nuevos_mp = [mp.get('id') for mp in materias_primas_nuevas if mp.get('id')]
                ids_nuevos_pp = [pp.get('producto') for pp in productos_nuevos if pp.get('producto')]

                print(f'ids_nuevos_pp:{ids_nuevos_pp}')

                vale_dev_mp = None
                vale_sol_mp = None
                vale_dev_pp = None
                vale_sol_pp = None
                
                # 5. Eliminar materias primas que ya no están
                for mp_actual in materias_actuales:
                    if str(mp_actual.id) not in ids_nuevos_mp:
                        if not vale_dev_mp:
                            vale_dev_mp = Vale_Movimiento_Almacen.objects.create(
                                tipo='Devolución',
                                destino=mp_actual.vale.almacen.nombre,
                                origen=produccion.planta.nombre,
                                entrada=False,
                                almacen=mp_actual.vale.almacen,
                                lote_No=produccion.lote,
                                estado='confirmado',
                                descripcion=f'Devolución por edición de producción {produccion.lote}',
                                despachado_por=request.user.first_name
                            )
                        Movimiento_MP.objects.create(
                            materia_prima=mp_actual.inv_materia_prima,
                            cantidad=mp_actual.cantidad_materia_prima,
                            vale=vale_dev_mp
                        )
                        mp_actual.delete()  # Eliminar en lugar de poner cantidad 0

                # 6. Eliminar productos que ya no están
                for pp_actual in productos_actuales:
                    print('En ciclo de productos actuales')
                    if self._normalizar_uuid(pp_actual.producto.id) not in ids_nuevos_pp:
                        print("Un actual que no está en los nuevos. Encontré uno nuevo")
                        if not vale_dev_pp:
                            vale_dev_pp = Vale_Movimiento_Almacen.objects.create(
                                tipo='Devolución',
                                destino=pp_actual.vale.almacen.nombre,
                                origen=produccion.planta.nombre,
                                entrada=False,
                                almacen=pp_actual.vale.almacen,
                                lote_No=produccion.lote,
                                estado='confirmado',
                                descripcion=f'Devolución por edición de producción {produccion.lote}',
                                despachado_por=request.user.first_name
                            )
                        # Asumiendo que tienes Movimiento_Producto (crea el modelo si no existe)
                        Movimiento_Prod.objects.create(
                                producto=pp_actual.producto,
                                cantidad=pp_actual.cantidad_producto,
                                vale=vale_dev_pp
                        )
                        print("Voy a borrar pp_actual")
                        pp_actual.delete()
                
                # 7. Actualizar o crear materias primas
                for mp_data in materias_primas_nuevas:
                    # Normalizar UUID
                    materia_prima_id = self._normalizar_uuid(mp_data['materia_prima'])
                    almacen_id = self._normalizar_uuid(mp_data['almacen'])
                    
                    materia_prima_obj = get_object_or_404(MateriaPrima, id=materia_prima_id)
                    almacen_obj = get_object_or_404(Almacen, id=almacen_id)
                    
                    # Obtener inventario (Inv_Mat_Prima)
                    inventario_mp = Inv_Mat_Prima.objects.filter(
                        materia_prima=materia_prima_obj,
                        almacen=almacen_obj
                    ).first()
                    
                    if not inventario_mp:
                        raise ValueError(f'No hay inventario de {materia_prima_obj.nombre} en {almacen_obj.nombre}')
                    
                    nueva_cantidad = Decimal(str(mp_data['cantidad']))
                    
                    if mp_data.get('id'):  # Actualizar existente
                        mp_existente = Prod_Inv_MP.objects.get(id=mp_data['id'])
                        cantidad_anterior = mp_existente.cantidad_materia_prima
                        diferencia = nueva_cantidad - cantidad_anterior
                        
                        if diferencia != 0:
                            if diferencia > 0:  # Aumenta cantidad
                                if inventario_mp.cantidad < diferencia:
                                    raise ValueError(f'Inventario insuficiente de {materia_prima_obj.nombre}')
                                if not vale_sol_mp:
                                    vale_sol_mp = Vale_Movimiento_Almacen.objects.create(
                                        tipo='Solicitud',
                                        entrada=False,
                                        almacen=almacen_obj,
                                        origen=produccion.planta.nombre,
                                        lote_No=produccion.lote,
                                        estado='confirmado',
                                        despachado_por=request.user.first_name
                                    )
                                Prod_Inv_MP.objects.create(
                                    lote_prod=produccion,
                                    inv_materia_prima=inventario_mp,
                                    cantidad_materia_prima=diferencia,
                                    almacen=almacen_obj,
                                    vale=vale_sol_mp
                                )
                            elif diferencia < 0:  # Disminuye cantidad
                                if not vale_dev_mp:
                                    vale_dev_mp = Vale_Movimiento_Almacen.objects.create(
                                        tipo='Devolución',
                                        destino=almacen_obj.nombre,
                                        origen=produccion.planta.nombre,
                                        entrada=False,
                                        almacen=almacen_obj,
                                        lote_No=produccion.lote,
                                        estado='confirmado',
                                        descripcion=f'Devolución por edición de producción {produccion.lote}',
                                        despachado_por=request.user.first_name
                                    )
                                Movimiento_MP.objects.create(
                                    materia_prima=inventario_mp,
                                    cantidad=abs(diferencia),
                                    vale=vale_dev_mp
                                )
                            
                            mp_existente.cantidad_materia_prima = nueva_cantidad
                            mp_existente.save()
                    else:  # Crear nueva
                        if inventario_mp.cantidad < nueva_cantidad:
                            raise ValueError(f'Inventario insuficiente de {materia_prima_obj.nombre}')
                        
                        if not vale_sol_mp:
                            vale_sol_mp = Vale_Movimiento_Almacen.objects.create(
                                tipo='Solicitud',
                                entrada=False,
                                almacen=almacen_obj,
                                origen=produccion.planta.nombre,
                                lote_No=produccion.lote,
                                estado='confirmado',
                                despachado_por=request.user.first_name
                            )
                        
                        Prod_Inv_MP.objects.create(
                            lote_prod=produccion,
                            inv_materia_prima=inventario_mp,
                            cantidad_materia_prima=nueva_cantidad,
                            almacen=almacen_obj,
                            vale=vale_sol_mp
                        )
                
                # 8. Actualizar o crear productos (insumos)
                for pp_data in productos_nuevos:
                    print('En ciclo de productos nuevos')
                    # Normalizar UUID
                    producto_id = self._normalizar_uuid(pp_data['producto'])
                    almacen_id = self._normalizar_uuid(pp_data['almacen'])
                    print(f'producto_id: {producto_id}')
                    #producto_catalogo = get_object_or_404(Producto, id=producto_id)
                    almacen_obj = get_object_or_404(Almacen, id=almacen_id)
                    
                    # Obtener inventario (Inv_Producto)
                    """ inventario_pp = Inv_Producto.objects.filter(
                        producto=producto_catalogo,
                        almacen=almacen_obj
                    ).first() """

                    inventario_pp = get_object_or_404(Inv_Producto, id=producto_id)
                    
                    if not inventario_pp:
                        raise ValueError(f'Error al acceder a ese inventario')
                    
                    nueva_cantidad = Decimal(str(pp_data['cantidad']))
                    
                    if pp_data.get('id'):  # Actualizar existente
                        print(pp_data['id'])
                        pp_id = self._normalizar_uuid(pp_data['id'])
                        pp_existente = Prod_Inv_Producto.objects.get(id=pp_id)
                        cantidad_anterior = pp_existente.cantidad_producto
                        diferencia = nueva_cantidad - cantidad_anterior
                        
                        if diferencia != 0:
                            if diferencia > 0:  # Aumenta cantidad
                                if inventario_pp.cantidad < diferencia:
                                    raise ValueError(f'Inventario insuficiente de {inventario_pp.producto.nombre_comercial}')
                                if not vale_sol_pp:
                                    vale_sol_pp = Vale_Movimiento_Almacen.objects.create(
                                        tipo='Solicitud',
                                        entrada=False,
                                        almacen=almacen_obj,
                                        origen=produccion.planta.nombre,
                                        lote_No=produccion.lote,
                                        estado='confirmado',
                                        despachado_por=request.user.first_name
                                    )
                                Prod_Inv_Producto.objects.create(
                                    lote_prod=produccion,
                                    producto=inventario_pp,
                                    cantidad_producto=diferencia,
                                    almacen=almacen_obj,
                                    vale=vale_sol_pp
                                )
                            elif diferencia < 0:  # Disminuye cantidad
                                if not vale_dev_pp:
                                    vale_dev_pp = Vale_Movimiento_Almacen.objects.create(
                                        tipo='Devolución',
                                        destino=almacen_obj.nombre,
                                        origen=produccion.planta.nombre,
                                        entrada=False,
                                        almacen=almacen_obj,
                                        lote_No=produccion.lote,
                                        estado='confirmado',
                                        despachado_por=request.user.first_name
                                    )
                            
                            pp_existente.cantidad_producto = nueva_cantidad
                            pp_existente.save()
                    else:  # Crear nueva
                        if inventario_pp.cantidad < nueva_cantidad:
                            raise ValueError(f'Inventario insuficiente de {inventario_pp.producto.nombre_comercial}')
                        
                        if not vale_sol_pp:
                            vale_sol_pp = Vale_Movimiento_Almacen.objects.create(
                                tipo='Solicitud',
                                entrada=False,
                                almacen=almacen_obj,
                                origen=produccion.planta.nombre,
                                lote_No=produccion.lote,
                                estado='confirmado',
                                despachado_por=request.user.first_name
                            )
                        
                        Prod_Inv_Producto.objects.create(
                            lote_prod=produccion,
                            producto=inventario_pp,
                            cantidad_producto=nueva_cantidad,
                            almacen=almacen_obj,
                            vale=vale_sol_pp
                        )
                
                # Guardar producción
                produccion.save()
                
                # Limpiar sesión
                if 'editar_produccion_data' in request.session:
                    del request.session['editar_produccion_data']
                    request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'message': 'Producción actualizada exitosamente',
                    'redirect_url': reverse('produccion_detail', args=[produccion.id])
                })
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'errors': f'Error al guardar: {str(e)}'})
    
    def _normalizar_uuid(self, valor):
        """Elimina guiones de un UUID si los tiene"""
        if not valor:
            return valor
        valor_str = str(valor)
        if '-' in valor_str and len(valor_str.replace('-', '')) == 32:
            return valor_str.replace('-', '')
        return valor_str
    
    def procesar_materias_primas(self, post_data):
        """Procesa las materias primas del formulario"""
        materias_primas = []
        
        def get_value(data, key):
            if isinstance(data, dict):
                return data.get(key)
            elif hasattr(data, 'get'):
                return data.get(key)
            return None
        
        i = 0
        while True:
            id_key = f'materias_primas[{i}][id]'
            materia_key = f'materias_primas[{i}][materia_prima]'
            cantidad_key = f'materias_primas[{i}][cantidad]'
            almacen_key = f'materias_primas[{i}][almacen]'
            
            materia_prima_id = get_value(post_data, materia_key)
            
            if not materia_prima_id:
                break
            
            mp_id = get_value(post_data, id_key)
            cantidad_str = get_value(post_data, cantidad_key)
            almacen_id = get_value(post_data, almacen_key)
            
            if not all([materia_prima_id, cantidad_str, almacen_id]):
                i += 1
                continue
            
            try:
                cantidad = Decimal(str(cantidad_str))
                
                # Normalizar UUIDs
                materia_prima_id = self._normalizar_uuid(materia_prima_id)
                almacen_id = self._normalizar_uuid(almacen_id)
                
                materia_prima_obj = get_object_or_404(MateriaPrima, id=materia_prima_id)
                costo_mp = float(cantidad) * float(materia_prima_obj.costo)
                
                mp_data = {
                    'id': mp_id if mp_id else None,
                    'materia_prima': materia_prima_id,
                    'cantidad': cantidad,
                    'almacen': almacen_id,
                    'costo': costo_mp,
                }
                materias_primas.append(mp_data)
                
            except Exception as e:
                raise ValueError(f'Error en materia prima {i}: {str(e)}')
            
            i += 1
        
        return materias_primas

    def procesar_productos(self, post_data):
        """Procesa los productos del formulario"""
        productos = []
        print('En procesar pruductos')
        print(post_data)
        def get_value(data, key):
            if isinstance(data, dict):
                return data.get(key)
            elif hasattr(data, 'get'):
                return data.get(key)
            return None
        
        i = 0
        while True:
            id_key = f'productos[{i}][id]'
            producto_key = f'productos[{i}][producto]'
            cantidad_key = f'productos[{i}][cantidad]'
            almacen_key = f'productos[{i}][almacen]'
            
            producto_id = get_value(post_data, producto_key)
            
            if not producto_id:
                print('No encontre el id')
                break
            else:
                print(f'producto id: {producto_id}')
                            
            pp_id = get_value(post_data, id_key)
            cantidad_str = get_value(post_data, cantidad_key)
            almacen_id = get_value(post_data, almacen_key)
            
            if not all([producto_id, cantidad_str, almacen_id]):
                i += 1
                continue
            
            try:
                cantidad = Decimal(str(cantidad_str))
                
                # Normalizar UUIDs
                producto_id = self._normalizar_uuid(producto_id)
                almacen_id = self._normalizar_uuid(almacen_id)
                
                producto_obj = get_object_or_404(Inv_Producto, id=producto_id)
                
                costo_pp = float(cantidad) * float(producto_obj.producto.costo)
                
                pp_data = {
                    'id': pp_id if pp_id else None,
                    'producto': producto_id,
                    'cantidad': cantidad,
                    'almacen': almacen_id,
                    'costo': costo_pp,
                }
                productos.append(pp_data)
                print(pp_data)
                
            except Exception as e:
                raise ValueError(f'Error en producto {i}: {str(e)}')
            
            i += 1
        print(f'Productos al final {productos}')
        return productos #
    
#funcionalidades para insertar pruebas químicas externas, emitidas por archivo.
@login_required
def subir_pruebas_quimicas(request, pk):
    """View para subir archivo de pruebas químicas"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if request.method == 'POST':
        form = SubirPruebasQuimicasForm(request.POST, request.FILES, instance=produccion)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Archivo de pruebas químicas subido correctamente para {produccion.lote}')
            produccion.estado = 'Evaluada'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Archivo subido correctamente',
                    'nombre_archivo': produccion.nombre_archivo_pruebas()
                })
            
            return redirect('produccion_list')
        else:
            messages.error(request, 'Error al subir el archivo')
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

@login_required
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

@login_required
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
        
        messages.success(request, f'Archivo de pruebas químicas eliminado para {produccion.lote}')
    else:
        messages.warning(request, 'No hay archivo para eliminar')
    
    return redirect('produccion_list')

###---Registro de pruebas quimicas---###

@login_required
def crear_prueba_quimica(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)

    if produccion.pruebas_quimicas.exists():
        return redirect('detalle_prueba_quimica', pk=pk)

    if request.method == 'POST':
        # Usar el form para validar los datos
        form = PruebaQuimicaForm(request.POST, request.FILES)
        
        fecha_prueba = request.POST.get('fecha_prueba')
        fecha_vencimiento = request.POST.get('fecha_vencimiento')

        if not fecha_prueba:
            messages.error(request, 'La fecha de prueba es obligatoria')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
                'form': form,
            })

        # Verificar que exista al menos un parámetro
        parametro_keys = [k for k in request.POST.keys() if k.startswith('parametro_')]
        if not parametro_keys:
            messages.error(request, 'Debe agregar al menos un parámetro')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
                'form': form,
            })

        #fecha_vencimiento = request.POST.get('fecha_vencimiento') or None
        observaciones = request.POST.get('observaciones', '')

        try:
            with transaction.atomic():
                prueba = PruebaQuimica.objects.create(
                    nomenclador_prueba=f"{produccion.lote}-{produccion.catalogo_producto.nombre_comercial}",
                    produccion=produccion,
                    fecha_prueba=fecha_prueba,                    
                    observaciones=observaciones,
                    estado="En Proceso",
                )
                
                parametros_procesados = 0
                advertencias = []

                for key in parametro_keys:
                    index = key.split('_')[1]
                    parametro_id = request.POST.get(f'parametro_{index}')
                    valor_medido = request.POST.get(f'valor_medido_{index}')

                    if not parametro_id or valor_medido is None:
                        advertencias.append(f'Parámetro {index}: datos incompletos')
                        continue

                    try:
                        parametro = ParametroPrueba.objects.get(id=parametro_id)
                    except ParametroPrueba.DoesNotExist:
                        advertencias.append(f'Parámetro {index}: no existe')
                        continue

                    # ===== PROCESAMIENTO SEGÚN TIPO =====
                    if parametro.tipo == 'organoleptico':
                        # 1. Guardar valor_medido exactamente como lo ingresó el usuario
                        # 2. Obtener cumplimiento del checkbox (true si está marcado, false si no)
                        cumplimiento = request.POST.get(f'cumplimiento_{index}') == 'on'
                        
                        DetallePruebaQuimica.objects.create(
                            prueba=prueba,
                            parametro=parametro,
                            valor_medido=valor_medido.strip(),      # texto libre
                            cumplimiento=cumplimiento,             # booleano
                        )
                        parametros_procesados += 1

                    else:  # fisico, quimico, microbiologico
                        # Validar que el valor sea numérico
                        try:
                            valor_decimal = Decimal(str(valor_medido).replace(',', '.'))
                        except (InvalidOperation, ValueError):
                            advertencias.append(f'{parametro.nombre}: "{valor_medido}" no es un número válido')
                            continue

                        # Validar rangos (solo advertencia, no impide guardar)
                        if parametro.valor_minimo is not None and valor_decimal < parametro.valor_minimo:
                            advertencias.append(f'{parametro.nombre}: valor por debajo del mínimo ({parametro.valor_minimo})')
                        if parametro.valor_maximo is not None and valor_decimal > parametro.valor_maximo:
                            advertencias.append(f'{parametro.nombre}: valor por encima del máximo ({parametro.valor_maximo})')

                        # Crear detalle (el cumplimiento se calculará automáticamente en el modelo)
                        DetallePruebaQuimica.objects.create(
                            prueba=prueba,
                            parametro=parametro,
                            valor_medido=str(valor_decimal),  # guardamos como string pero numérico
                            # cumplimiento no se envía, el modelo lo calcula en save()
                        )
                        parametros_procesados += 1

                if parametros_procesados == 0:
                    raise ValueError('No se pudo guardar ningún parámetro')

                # ACTUALIZAR LA FECHA DE VENCIMIENTO DE LA PRODUCCIÓN
                #fecha_vencimiento = form.cleaned_data.get('fecha_vencimiento')
                fecha_prueba_dt = datetime.strptime(fecha_prueba, '%Y-%m-%d').date()
                
                if fecha_vencimiento and fecha_vencimiento.strip():
                    fecha_vencimiento_dt = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
    
                    if fecha_vencimiento_dt <= fecha_prueba_dt:
                        messages.error(request, 'La fecha de vencimiento debe ser posterior a la fecha de prueba')
                        raise ValueError('Fecha de vencimiento inválida')
    
                    produccion.fecha_vencimiento = fecha_vencimiento
                    messages.info(request, f'Fecha de vencimiento actualizada: {fecha_vencimiento}')
                else:
                    ANIOS_VENCIMIENTO = 2  # ← Configura aquí los años que necesitas
                    
                    # Opción 1: Usando relativedelta (más preciso, respeta fechas como 29/02)
                    fecha_vencimiento_dt = fecha_prueba_dt + relativedelta(years=ANIOS_VENCIMIENTO)
                    
                    produccion.fecha_vencimiento = fecha_vencimiento_dt
                    messages.info(request, f'Fecha de vencimiento calculada automáticamente ({ANIOS_VENCIMIENTO} años): {fecha_vencimiento_dt}')

                # Guardar la producción actualizada
                produccion.save(update_fields=['fecha_vencimiento'])
                
                # Mostrar advertencias si las hay
                for adv in advertencias:
                    messages.warning(request, adv)

                messages.success(request, f'Prueba creada con {parametros_procesados} parámetros')
                return redirect('detalle_prueba_quimica', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al crear la prueba: {str(e)}')
            # Log opcional
            # logger.exception("Error en creación de prueba química")
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
                'form': form,
            })
    else:
        form = PruebaQuimicaForm()
    # GET request
    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
        'produccion': produccion,
        'parametros_existentes': parametros_existentes,
        'form': form,
    })
    
@login_required
def detalle_prueba_quimica(request, pk):
    """Ver detalle de una prueba química"""
    produccion = get_object_or_404(Produccion, id=pk)

    almacenes = Almacen.objects.all()
    
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
        'almacenes': almacenes,
    }
    
    return render(request, 'produccion/prueba_quimica/detalle_prueba_quimica.html', context)

@login_required
@csrf_exempt  # Si usas CSRF token en el header, no es necesario; pero mejor mantener protección
def agregar_parametros_prueba(request, prueba_id):
    """Agrega múltiples parámetros a una prueba química existente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    try:
        prueba = PruebaQuimica.objects.get(id=prueba_id)
    except PruebaQuimica.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prueba no encontrada'}, status=404)

    try:
        data = json.loads(request.body)
        parametros_list = data.get('parametros', [])
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Datos inválidos'}, status=400)

    if not parametros_list:
        return JsonResponse({'success': False, 'message': 'No se enviaron parámetros'}, status=400)

    creados = 0
    errores = []

    for item in parametros_list:
        parametro_id = item.get('parametro_id')
        valor_medido = item.get('valor_medido', '').strip()
        observaciones = item.get('observaciones', '')
        cumplimiento = item.get('cumplimiento')  # Puede ser True/False o None

        if not parametro_id or not valor_medido:
            errores.append(f'Parámetro {creados+1}: Datos incompletos')
            continue

        try:
            parametro = ParametroPrueba.objects.get(id=parametro_id, activo=True)
        except ParametroPrueba.DoesNotExist:
            errores.append(f'Parámetro ID {parametro_id} no existe')
            continue

        # --- Procesamiento según tipo ---
        if parametro.tipo == 'organoleptico':
            # Valor medido: texto libre, cumplimiento: booleano (si no se envía, asumir False)
            cumple = cumplimiento if isinstance(cumplimiento, bool) else False
            DetallePruebaQuimica.objects.create(
                prueba=prueba,
                parametro=parametro,
                valor_medido=valor_medido,
                cumplimiento=cumple,
                observaciones=observaciones
            )
            creados += 1

        else:  # físico, químico, microbiológico
            # Validar que el valor sea numérico
            try:
                valor_decimal = Decimal(valor_medido.replace(',', '.'))
            except (InvalidOperation, ValueError):
                errores.append(f'{parametro.nombre}: "{valor_medido}" no es un número válido')
                continue

            # Crear detalle (el modelo calculará el cumplimiento automáticamente en save)
            DetallePruebaQuimica.objects.create(
                prueba=prueba,
                parametro=parametro,
                valor_medido=str(valor_decimal),
                observaciones=observaciones
            )
            creados += 1

    mensaje = f'Se agregaron {creados} parámetros correctamente.'
    if errores:
        mensaje += ' Algunos parámetros presentaron errores: ' + '; '.join(errores[:3])

    return JsonResponse({
        'success': True,
        'message': mensaje,
        'creados': creados,
        'errores': errores
    })
    
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
        """Agregar multiples parametros a una prueba"""
        prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
        
        parametros_data = request.POST.get('parametros')
        
        if not parametros_data:
            return JsonResponse({
                'success': False,
                'message': 'No se recibieron datos de parámetros'
            })
        
        # Parsear JSON
        try:
            parametros = json.loads(parametros_data)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en formato JSON: {str(e)}'
            })
        
        for item in parametros:
            parametro = get_object_or_404(ParametroPrueba, id=item['parametro_id'])
            
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
            'message': f'Parámetros agregados correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def agregar_parametros_pruebaO(request, prueba_id):

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

        parametro_prueba.valor_medido = nuevo_valor.replace(',','.')

        parametro_prueba.save()
       
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
    almacen_destino_id = request.POST.get('almacen_destino')

    # Validaciones
    if not decision_final:
        messages.error(request, 'Debe seleccionar una decisión final.')
        return render(request, 'produccion/detalle_prueba_quimica.html', {
            'prueba': prueba,
            'parametros': prueba.detalles.all(),
            'error': True
        })

    if decision_final == 'Aprobada' and not almacen_destino_id:
        return JsonResponse({
            'success': False,
            'message': 'Debe seleccionar un almacén destino para el producto aprobado.'
        }, status=400)
        
    try:
        with transaction.atomic():
            # Actualizar prueba
            cantidad = 0
            prueba.estado = decision_final
            if prueba.estado == 'Aprobada':
                prueba.resultado_final = True
                prueba.produccion.estado = 'Concluida-Satisfactoria'
                tipo = 'Producción terminada'
                estado='confirmado'
            elif prueba.estado == 'Rechazada':
                prueba.resultado_final = False
                prueba.produccion.estado = 'Concluida-Rechazada'
                tipo = 'Producción rechazada'
                estado='rechazado'
                cantidad = prueba.produccion.cantidad_real
            prueba.produccion.save() 
            # Aquí creo vale de produccion terminada, envío solicitud de entrada a Almacen y envío notificación a Admin
            almacen_destino = get_object_or_404(Almacen, id=almacen_destino_id)
            vale = Vale_Movimiento_Almacen.objects.create(
                    origen = tipo + ' en ' + prueba.produccion.planta.nombre,
                    almacen = almacen_destino,
                    destino = almacen_destino.nombre, # Aquí va el nuevo parametro almacen desde el modal 
                    entrada = False,
                    tipo = tipo,
                    estado=estado,
                    lote_No = prueba.produccion.lote,
                    descripcion = 'Producción terminada de ' + prueba.produccion.catalogo_producto.nombre_comercial + ' lote ' + prueba.produccion.lote,
                    despachado_por = request.user.first_name,
            )
                
            #Este es el movimiento especifico del producto
            formato = Formato.objects.filter(capacidad = 0).first()

            nuevo_prod, created = Inv_Producto.objects.get_or_create(
                almacen = almacen_destino,
                cantidad = cantidad,
                lote = prueba.produccion.lote,
                producto = prueba.produccion.catalogo_producto,
                estado = 'inventario' if prueba.estado == 'Aprobada' else 'noconforme',
                formato = formato
            )

            Movimiento_Prod.objects.create(
                    vale=vale,
                    producto=nuevo_prod,
                    cantidad=prueba.produccion.cantidad_real,
                    lote=prueba.produccion.lote
            )

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
        return JsonResponse({
            'success': True,
            'message': f'Prueba {prueba.estado.lower()} correctamente.',
            'redirect_url': reverse('detalle_prueba_quimica', args=[prueba.produccion.id])
        })    

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al concluir la prueba: {str(e)}'
        }, status=500)    

@login_required
def calcular_resultados_prueba(request, prueba_id):
    """Recalcular resultados de todos los parámetros"""
    prueba = get_object_or_404(PruebaQuimica, id=prueba_id)
    detal_prueba = DetallePruebaQuimica.objects.filter(prueba=prueba).all()
    
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