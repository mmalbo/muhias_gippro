# views.py
import os
from django.conf import settings
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
from django.db.models import Q, Sum, F
from django.db import transaction
from decimal import Decimal, InvalidOperation
import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
import urllib.parse

from collections import OrderedDict
from .models import Planta
from .models import Produccion, Prod_Inv_MP, PruebaQuimica, ParametroPrueba, DetallePruebaQuimica
from materia_prima.models import MateriaPrima
from inventario.models import Inv_Mat_Prima, Inv_Producto
from producto.models import Producto
from envase_embalaje.models import Formato
from nomencladores.almacen.models import Almacen
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_Prod
from .forms import (ProduccionForm, MateriaPrimaForm, 
    SubirPruebasQuimicasForm, CancelarProduccionForm, PruebaQuimicaForm, 
    DetallePruebaForm, AprobarPruebaForm, ParametroPruebaForm, BuscarParametroForm)


class ProduccionListView(ListView):
    model = Produccion
    template_name = 'produccion/list.html'
    context_object_name = 'produccions'
    # Opción A: Usando ordering en la vista
    ordering = ['-fecha_creacion']

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
            
        context = {
            'produccion_form': produccion_form,
            'materia_prima_form': materia_prima_form,
            'materias_primas_json': self.get_materias_primas_json(),
            'produccion_base': self._obtener_produccion_base(request),
            'materias_primas_precargadas': datos_precargados.get('materias_primas_precargadas', []) if datos_precargados else [],
        }
        return render(request, self.template_name, context)

    def _obtener_datos_precargados(self, request):
        """Extrae datos pre-cargados de query parameters o sesion"""
        datos = {}
        
        # 1. Verificar query parameters (viene de reutilizar_produccion)
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
                    
                    # Materias primas (para mostrar como sugerencia)
                    'materias_primas_precargadas': self._obtener_materias_primas_precargadas(produccion_base),
                }
            except Produccion.DoesNotExist:
                pass
        
        # 2. También verificar si ya hay datos en sesión
        elif 'produccion_data' in request.session:
            session_data = request.session['produccion_data']
            if 'produccion_base_id' in session_data:
                datos.update(session_data)
        
        return datos
    
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
            catalogo_producto_id = self.procesar_producto(request)
            if not catalogo_producto_id:
                return JsonResponse({
                    'success': False, 
                    'errors': 'Error al procesar el producto'
                })
            
            # Extraer solo datos primitivos para la sesión
            session_data = {
                #'lote': request.POST.get('lote'),
                'catalogo_producto_id': str(catalogo_producto_id),  # Guardar como string
                'cantidad_estimada': request.POST.get('cantidad_estimada'),
                'prod_result': request.POST.get('prod_result'),
                'planta_id': request.POST.get('planta'),  # Guardar el ID como string
            }            
            # Guardar en sesión
            #request.session['produccion_data'] = session_data
            request.session['produccion_data'].update(session_data)
            request.session.modified = True
            return JsonResponse({'success': True, 'step': 2})
        else:
            print("Errores en formulario:", produccion_form.errors)
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
                print(f"Producto con ID {catalogo_producto_id} no existe")
                return None
        else:
            print("No esta el producto ni producto existente")
            return None

    def procesar_paso_2(self, request):
        # Recuperar datos del paso 1 de la sesión
        
        produccion_data = request.session.get('produccion_data', {})
        if not produccion_data:
            return JsonResponse({
                'success': False, 
                'errors': 'Datos de produccion no encontrados. Por favor, complete el paso 1 nuevamente.'
            })
           
        # Verificar que'lote',  los datos minimos esten presentes
        required_fields = ['catalogo_producto_id', 'cantidad_estimada', 'planta_id']
        missing_fields = [field for field in required_fields if not produccion_data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False, 
                'errors': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            })

        # SOLUCION: Asegurar que post_data sea un diccionario, no bytes
        try:
            # Verificar si es un QueryDict (lo normal en Django)
            if hasattr(request.POST, 'dict'):
                post_data = request.POST.dict()  # Convertir a dict regular
            else:
                # Si no es QueryDict, podría ser bytes (caso del error)
                if isinstance(request.body, bytes):
                    # Intentar decodificar como JSON
                    try:
                        post_data = json.loads(request.body.decode('utf-8'))
                    except json.JSONDecodeError:
                        # Si no es JSON, podría ser form-urlencoded
                        from urllib.parse import parse_qs
                        parsed = parse_qs(request.body.decode('utf-8'))
                        post_data = {}
                        for key, values in parsed.items():
                            if values:
                                post_data[key] = values[0]
                else:
                    # Intentar convertir a dict de alguna otra manera
                    post_data = dict(request.POST) if hasattr(request.POST, '__dict__') else {}
        except Exception as e:
            post_data = {}
    
        # Procesar materias primas
        materias_primas = self.procesar_materias_primas(post_data)
        # materias_primas = self.procesar_materias_primas(request.POST)
        if not materias_primas:
            return JsonResponse({'success': False, 'errors': 'Debe agregar al menos una materia prima'})
        
        try:
            # Obtener la instancia de Planta
            planta_instance = Planta.objects.get(id=produccion_data['planta_id'])
            catalogo_producto_instance = Producto.objects.get(id=produccion_data['catalogo_producto_id'])
            # GENERAR LOTE CON EL NUEVO FORMATO
            cantidad_estimada = float(produccion_data['cantidad_estimada'])
            lote_generado = Produccion.generar_lote(
                catalogo_producto=catalogo_producto_instance,
                planta=planta_instance,
                cantidad_estimada=cantidad_estimada
            )
            print(lote_generado)

            if produccion_data['prod_result']: 
                product=True
            else:
                product=False

            # Verificar que el lote no exista (por si acaso)
            intentos = 0
            lote_final = lote_generado
            
            while Produccion.objects.filter(lote=lote_final).exists() and intentos < 10:
                intentos += 1
                # Si por alguna rareza existe, añadir un sufijo
                lote_final = f"{lote_generado}-{intentos:02d}"
            
            costo_prod = 0
            for mp_data in materias_primas:
                costo_prod += Decimal(mp_data['costo'])

            # Obtener producción base si existe
            produccion_base = None
            if produccion_data.get('produccion_base_id'):
                produccion_base = Produccion.objects.get(id=produccion_data['produccion_base_id'])
            else:
                print("No esta llegando la produccion base")

            print(produccion_base)
            # Guardar producción
            produccion = Produccion.objects.create(
                lote=lote_final,
                catalogo_producto=catalogo_producto_instance,
                prod_result=product,
                cantidad_estimada=Decimal(produccion_data['cantidad_estimada']),
                costo=costo_prod,#Decimal(produccion_data['costo']),                
                planta=planta_instance,
                estado='Planificada',
                # ESTABLECER RELACIÓN CON PRODUCCIÓN BASE
                produccion_base=produccion_base,
                observaciones_reutilizacion=produccion_data.get('observaciones_reutilizacion', '')
            )

            #generar un vale de almacen tipo solicitud costo_mp = mp_data['costo']
            id_almacen = materias_primas[0]['almacen']
            almacen_obj = Almacen.objects.get(id=id_almacen)
            vale = Vale_Movimiento_Almacen.objects.create(
                tipo = 'Solicitud',
                entrada = False,
                almacen = almacen_obj
            )

            # Guardar relación con materias primas
            for mp_data in materias_primas:
                almacen_o=Almacen.objects.get(id=mp_data['almacen'])
                mat_pri_o=MateriaPrima.objects.get(id=mp_data['materia_prima'])
                if not vale.almacen:
                    vale.almacen = almacen_o
                Prod_Inv_MP.objects.create(
                    lote_prod=produccion,
                    inv_materia_prima=mat_pri_o,
                    cantidad_materia_prima=mp_data['cantidad'],
                    almacen=almacen_o,
                    vale = vale
                )
                
            # Limpiar sesión
            if 'produccion_data' in request.session:
                del request.session['produccion_data']
                request.session.modified = True

            # Mensaje específico para reutilización
            if produccion.produccion_base:
                message = f'Produccion creada reutilizando {produccion_base.lote} como base'
            else:
                message = 'Produccion creada exitosamente'
            
            return JsonResponse({
                'success': True, 
                'message': message, 
                'produccion_id': produccion.id,
                'redirect_url': reverse('produccion_list')  # Ajusta esta URL
            })
            
        #except Planta.DoesNotExist:
            #return JsonResponse({'success': False, 'errors': 'La planta seleccionada no existe'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': f'Error al guardar: {str(e)}'})

    def get_materias_primas_json(self):
        materias_primas = MateriaPrima.objects.all().values(
            'id', 'nombre', 'tipo_materia_prima', 'conformacion', 'unidad_medida', 'concentracion', 'costo'
        )
        return list(materias_primas)

    def procesar_materias_primas(self, post_data):
        materias_primas = []
         
        # CASO 1: Si post_data es None o vacio
        if not post_data:
            print("post_data esta vacio")
            return []
    
        # CASO 2: Si es bytes (error original)
        if isinstance(post_data, bytes):
            print("post_data es bytes, convirtiendo...")
            try:
                import json
                post_data = json.loads(post_data.decode('utf-8'))
            except:
                try:
                    from urllib.parse import parse_qs
                    decoded = post_data.decode('utf-8')
                    parsed = parse_qs(decoded)
                    post_data = {}
                    for key, values in parsed.items():
                        if values:
                            post_data[key] = values[0]
                except Exception as e:
                    print(f"Error decodificando bytes: {e}")
                    return []
    
        # CASO 3: Si ya es dict o QueryDict, proceder normalmente
        i = 0
    
        # Función helper para obtener valores de manera segura
        def get_value(data, key):
            if isinstance(data, dict):
                return data.get(key)
            elif hasattr(data, 'get'):  # QueryDict también tiene .get()
                return data.get(key)
            else:
                # Último recurso: intentar acceso por índice
                try:
                    return data[key]
                except (TypeError, KeyError):
                    return None
    
        while True:
            materia_prima_key = f'materias_primas[{i}][materia_prima]'
            materia_prima_id = get_value(post_data, materia_prima_key)
        
            # Si no hay más materias primas, salir
            if not materia_prima_id:
                break
        
            cantidad_str = get_value(post_data, f'materias_primas[{i}][cantidad]')
            #almacen_id = get_value(post_data, f'materias_primas[{i}][almacen]')
        
            # Validar que todos los campos estén presentes
            if not all([materia_prima_id, cantidad_str]):
                print(f" Materia prima {i} incompleta, saltando...")
                i += 1
                continue
        
            try:
                # Convertir y validar
                cantidad = Decimal(str(cantidad_str))
                
                # Obtener objetos
                inv_materia_prima_obj = Inv_Mat_Prima.objects.get(id=materia_prima_id)
                almacen_obj = Almacen.objects.get(id=inv_materia_prima_obj.almacen.id)
            
                # Verificar inventarioInv_Mat_Prima.objects.get(materia_prima=materia_prima_obj, almacen=almacen_obj)
                if inv_materia_prima_obj:
                    try:
                        if cantidad > inv_materia_prima_obj.cantidad:
                            error_msg = f"Cantidad insuficiente de {inv_materia_prima_obj.materia_prima.nombre}"
                            print(f" {error_msg}")
                            raise ValueError(error_msg)
            
                        # Calcular costo
                        costo_mp = Decimal(str(inv_materia_prima_obj.materia_prima.costo)) * cantidad
            
                        materias_primas.append({
                            'materia_prima': inv_materia_prima_obj.materia_prima.id,
                            'cantidad': cantidad,
                            'almacen': almacen_obj.id,
                            'costo': costo_mp,
                            'materia_prima_obj': inv_materia_prima_obj.materia_prima,
                            'almacen_obj': almacen_obj
                        })
                    except (Inv_Mat_Prima.DoesNotExist, ValueError) as e:
                        print(f"Error con MP {i}: {e}")
                        # Relanzar para que sea capturado por procesar_paso_2
                        raise ValueError(f"Materia prima {i}: {str(e)}")


            except (MateriaPrima.DoesNotExist, Almacen.DoesNotExist, 
                    Inv_Mat_Prima.DoesNotExist, ValueError) as e:
                print(f"Error Fuera con MP {i}: {e}")
                # Relanzar para que sea capturado por procesar_paso_2
                raise ValueError(f"Materia prima {i}: {str(e)}")
            except Exception as e:
                print(f"Error inesperado con MP {i}: {e}")
                raise
        
            i += 1
    
        return materias_primas

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
        
        # 2. Calcular total de costos de materias primas
        costo_total_mp = produccion.costo
        
        # 3. Pruebas químicas asociadas
        pruebas_quimicas = produccion.pruebas_quimicas.all()  # Usando related_name
        
        # 4. Historial de cambios (si tienes model History)
        try:
            from django.contrib.admin.models import LogEntry
            historial = LogEntry.objects.filter(
                object_id=produccion.id,
                content_type__model='produccion'
            ).order_by('-action_time')[:10]
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
            costo_litro = produccion.costo / float(produccion.cantidad_estimada)
        else:
            costo_litro = produccion.costo / float(produccion.cantidad_real)
             
        
        # 5. Datos para gráficos o estadísticas
        datos_produccion = {
            'lote_base': produccion.produccion_base.lote if produccion.produccion_base else '',
            'costo_materias_primas': costo_total_mp,
            'costo_total': produccion.costo,
            'diferencia_costo': produccion.costo - costo_total_mp,
            'eficiencia': (produccion.cantidad_real or 0) / produccion.cantidad_estimada * 100 
            if produccion.cantidad_real else 0,
            'porcentaje_avance': porcentaje_avance,
            'costo_litro': costo_litro
        }
        
        # 6. Productos relacionados (si aplica)
        producto_relacionado = produccion.catalogo_producto
        
        context.update({
            'materias_primas': materias_primas,
            'costo_total_mp': costo_total_mp,
            'pruebas_quimicas': pruebas_quimicas,
            'historial': historial,
            'datos_produccion': datos_produccion,
            'producto_relacionado': producto_relacionado,
            'estados_disponibles': self.get_estados_disponibles(produccion),
            'puede_editar': self.puede_editar_produccion(produccion),
        })
        
        return context
    
    def get_estados_disponibles(self, produccion):
        """Retorna los estados a los que puede cambiar la producción"""
        estados = []
        estado_actual = produccion.estado
        
        if estado_actual == 'Planificada':
            estados = ['En proceso: Iniciando mezcla', 'Cancelada']
        elif estado_actual == 'En proceso: Iniciando mezcla':
            estados = ['En proceso: Agitado', 'Cancelada']
        elif estado_actual == 'En proceso: Agitado':
            estados = ['En proceso: Validación']
        elif estado_actual == 'En proceso: Validación':
            estados = ['Concluida-Satisfactoria', 'Concluida-Rechazada']
        
        return estados
    
    def puede_editar_produccion(self, produccion):
        """Determina si el usuario puede editar esta producción"""
        estados_editables = ['Planificada', 'En proceso: Iniciando mezcla']
        return produccion.estado in estados_editables and self.request.user.has_perm('app.change_produccion')

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

class EditarProduccionView(View):
    template_name = 'produccion/editar_produccion.html'
    
    def get(self, request, pk):
        # Obtener la producción existente
        print('En el get')
        produccion = get_object_or_404(Produccion, id=pk)
        print(produccion)
    
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
    
        # Obtener materias primas disponibles para el selector - ¡CORREGIDO!
        # Necesitas obtener los objetos completos con la información necesaria
        materias_disponibles = Inv_Mat_Prima.objects.select_related('materia_prima', 'almacen').filter(
            cantidad__gt=0,  # Solo las que tienen stock
            #materia_prima__activo=True   Asumiendo que tienes este campo
        )[:50]  # Limitar para evitar problemas de rendimiento
    
        # Formatear para el template - estructura que espera el frontend
        materias_disponibles_list = []
        for inv in materias_disponibles:
            materias_disponibles_list.append({
                'id': inv.id,
                'materia_prima_id': inv.materia_prima.id,
                'materia_prima_nombre': inv.materia_prima.nombre,
                'unidad_medida': inv.materia_prima.unidad_medida,
                'costo': float(inv.materia_prima.costo),
                'almacen_id': inv.almacen.id,
                'almacen_nombre': inv.almacen.nombre,
                'cantidad_disponible': float(inv.cantidad)
            })
    
            # Obtener almacenes para el selector
            almacenes = Almacen.objects.all()  # Asumiendo que tienes este filtro
            almacenes_list = [{'id': a.id, 'nombre': a.nombre} for a in almacenes]
    
            context = {
                'produccion': produccion,
                'materias_primas_actuales': materias_primas_actuales,
                'materias_primas_json': materias_primas_json,
                'materias_primas_disponibles': materias_disponibles,
                'materias_disponibles_json': materias_disponibles_list,
                'almacenes': almacenes,
                'almacenes_json': almacenes_list,
            }
    
        return render(request, self.template_name, context)

    def _obtener_materias_primas_json(self, materias_primas_actuales):
        """Convierte las materias primas actuales a JSON para el frontend"""
        materias = []
        print("🔍 En obtener materias primas existentes")
    
        for mp in materias_primas_actuales:
            # Obtener inventario actual
            inventario = Inv_Mat_Prima.objects.filter(
                materia_prima=mp.inv_materia_prima,
                almacen=mp.almacen
            ).first()
        
            # IMPORTANTE: mp.inv_materia_prima es el objeto Inv_Mat_Prima
            # Necesitamos acceder a materia_prima (el objeto MateriaPrima) a través de él
            materia_prima_obj = mp.inv_materia_prima
        
            materia_data = {
                'id': str(mp.id),  # ID de Prod_Inv_MP
                'inventario_id': str(mp.inv_materia_prima.id) if mp.inv_materia_prima else None,  # ID de Inv_Mat_Prima
                'materia_prima_id': str(materia_prima_obj.id),  # ID de MateriaPrima
                'materia_prima_nombre': materia_prima_obj.nombre,
                'cantidad': float(mp.cantidad_materia_prima),
                'almacen_id': str(mp.almacen.id),
                'almacen_nombre': mp.almacen.nombre,
                'unidad_medida': materia_prima_obj.unidad_medida,
                'costo_unitario': float(materia_prima_obj.costo),
                'costo_total': float(mp.cantidad_materia_prima) * materia_prima_obj.costo,
                'inventario_disponible': float(inventario.cantidad) if inventario else 0,
            }
        
            print(f"  ➕ Materia prima existente: {materia_data}")
            materias.append(materia_data)
        
        return materias
    
    def post(self, request, pk):
        
        produccion = get_object_or_404(Produccion, id=pk)
    
        # Recuperar datos de sesión o usar los actuales
        editar_data = request.session.get('editar_produccion_data', {})
        
        step = request.POST.get('step')
        print(f"🔍 POST recibido - step: {step}")
        print(f"🔍 POST data: {request.POST}")
        
        if step == '1':
            return self.procesar_paso_1(request, produccion)
        elif step == '2':
            return self.procesar_paso_2(request, produccion)
        else:
            return JsonResponse({'success': False, 'errors': 'Paso no válido'})
    
    def procesar_paso_1(self, request, produccion):
        """Actualizar cantidad estimada"""
        cantidad_estimada = request.POST.get('cantidad_estimada')
    
        print(f"🔍 procesar_paso_1 - POST data: {request.POST}")
        print(f"🔍 cantidad_estimada recibida: {cantidad_estimada}")
    
        if not cantidad_estimada:
            return JsonResponse({'success': False, 'errors': 'La cantidad estimada es obligatoria'})
    
        try:
            # Validar que sea un número positivo
            cantidad_decimal = Decimal(cantidad_estimada)
            if cantidad_decimal <= 0:
                return JsonResponse({'success': False, 'errors': 'La cantidad debe ser mayor a cero'})
        
            # Actualizar en sesión
            editar_data = request.session.get('editar_produccion_data', {})
            editar_data['cantidad_estimada'] = str(cantidad_decimal)
            request.session['editar_produccion_data'] = editar_data
            request.session.modified = True
        
            print(f"✅ Cantidad estimada guardada en sesión: {cantidad_decimal}")
        
            return JsonResponse({'success': True, 'step': 2})
        
        except (ValueError, InvalidOperation) as e:
            return JsonResponse({'success': False, 'errors': f'La cantidad no es válida: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': f'Error: {str(e)}'})
    
    def procesar_paso_2(self, request, produccion):
        """Actualizar materias primas"""
        # Procesar materias primas enviadas
        print(f"🔍 procesar_paso_2 - POST data: {request.POST}")
        try:
            materias_primas_nuevas = self.procesar_materias_primas(request.POST)
        except ValueError as e:
            return JsonResponse({'success': False, 'errors': str(e)})
        
        #if not materias_primas_nuevas:
        #    return JsonResponse({'success': False, 'errors': 'Debe agregar al menos una materia prima'})
        
        try:
            
            with transaction.atomic():
                # 1. Actualizar cantidad estimada
                editar_data = request.session.get('editar_produccion_data', {})
                if 'cantidad_estimada' in editar_data:
                    produccion.cantidad_estimada = Decimal(editar_data['cantidad_estimada'])
                
                # 2. Calcular nuevo costo total
                costo_total = sum(Decimal(str(mp['costo'])) for mp in materias_primas_nuevas)
                produccion.costo = costo_total
                
                # 3. Obtener materias primas actuales
                materias_actuales = Prod_Inv_MP.objects.filter(lote_prod=produccion)
                
                # 4. Identificar IDs de materias primas nuevas
                ids_nuevos = [mp.get('id') for mp in materias_primas_nuevas if mp.get('id')]
                
                # 5. Eliminar las que ya no están
                for mp_actual in materias_actuales:
                    if str(mp_actual.id) not in ids_nuevos:
                        mp_actual_obj=MateriaPrima.objects.get(id=mp_actual.inv_materia_prima.id)
                        # Devolver al inventario antes de eliminar
                        inventario = Inv_Mat_Prima.objects.filter(
                            materia_prima=mp_actual_obj,
                            almacen=mp_actual.almacen
                        ).first()
                        
                        if inventario:
                            inventario.cantidad -= mp_actual.cantidad_materia_prima
                            inventario.save()
                        
                        mp_actual.delete()
                
                # 6. Actualizar o crear nuevas materias primas
                vale = None
                for mp_data in materias_primas_nuevas:
                    materia_prima_obj = get_object_or_404(MateriaPrima, id=mp_data['materia_prima'])
                    almacen_obj = get_object_or_404(Almacen, id=mp_data['almacen'])
                    # Obtener inventario
                    inventario = Inv_Mat_Prima.objects.filter(
                        materia_prima=materia_prima_obj,
                        almacen=almacen_obj
                    ).first()
                    
                    if not inventario:
                        raise ValueError(f'No hay inventario de {materia_prima_obj.nombre} en {almacen_obj.nombre}')
                    
                    nueva_cantidad = Decimal(str(mp_data['cantidad']))
                    cantidad_anterior = Decimal('0')
                    
                    # Verificar si es una actualización o creación
                    if mp_data.get('id'):  # Actualizar existente
                        mp_existente = Prod_Inv_MP.objects.get(id=mp_data['id'])
                        cantidad_anterior = mp_existente.cantidad_materia_prima
                        
                        # Ajustar inventario
                        if nueva_cantidad > cantidad_anterior:
                            diferencia = nueva_cantidad - cantidad_anterior
                            if inventario.cantidad < diferencia:
                                raise ValueError(f'Inventario insuficiente de {materia_prima_obj.nombre}')
                            inventario.cantidad -= diferencia
                        else:
                            diferencia = cantidad_anterior - nueva_cantidad
                            inventario.cantidad += diferencia
                        
                        mp_existente.cantidad_materia_prima = nueva_cantidad
                        mp_existente.save()
                        
                    else:  # Crear nueva
                        if inventario.cantidad < nueva_cantidad:
                            raise ValueError(f'Inventario insuficiente de {materia_prima_obj.nombre}')
                        
                        inventario.cantidad -= nueva_cantidad
                        
                        # Crear o reutilizar vale
                        if not vale:
                            vale = Vale_Movimiento_Almacen.objects.create(
                                tipo='Solicitud',
                                entrada=False,
                                almacen=almacen_obj
                            )
                        
                        Prod_Inv_MP.objects.create(
                            lote_prod=produccion,
                            inv_materia_prima=materia_prima_obj,
                            cantidad_materia_prima=nueva_cantidad,
                            almacen=almacen_obj,
                            vale=vale
                        )
                    
                    inventario.save()
                
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
            return JsonResponse({'success': False, 'errors': f'Error al guardar: {str(e)}'})
    
    def procesar_materias_primas(self, post_data):
        """Procesa las materias primas del formulario"""
        materias_primas = []
        
        # Función helper para obtener valores
        def get_value(data, key):
            if isinstance(data, dict):
                return data.get(key)
            elif hasattr(data, 'get'):
                return data.get(key)
            return None
        
        i = 0
        while True:
            # Buscar por diferentes formatos posibles
            id_key = f'materias_primas[{i}][id]'
            materia_key = f'materias_primas[{i}][materia_prima]'
            cantidad_key = f'materias_primas[{i}][cantidad]'
            almacen_key = f'materias_primas[{i}][almacen]'
            
            # Intentar obtener materia prima
            materia_prima_id = get_value(post_data, materia_key)
            
            if not materia_prima_id:
                # Intentar con formato alternativo
                materia_prima_id = get_value(post_data, f'materias_primas[{i}].materia_prima')
            
            if not materia_prima_id:
                break
            
            # Obtener otros valores
            mp_id = get_value(post_data, id_key)
            cantidad_str = get_value(post_data, cantidad_key) or get_value(post_data, f'materias_primas[{i}].cantidad')
            almacen_id = get_value(post_data, almacen_key) or get_value(post_data, f'materias_primas[{i}].almacen')
            
            if not all([materia_prima_id, cantidad_str, almacen_id]):
                i += 1
                continue
            
            try:
                cantidad = Decimal(str(cantidad_str))
                
                # Obtener objetos y calcular costo
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

#Salva del crear prueba quimica
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

def crear_prueba_quimica(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    parametros_existentes = ParametroPrueba.objects.filter(activo=True)

    if produccion.pruebas_quimicas.exists():
        return redirect('detalle_prueba_quimica', pk=pk)

    if request.method == 'POST':
        fecha_prueba = request.POST.get('fecha_prueba')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None
        observaciones = request.POST.get('observaciones', '')

        if not fecha_prueba:
            messages.error(request, 'La fecha de prueba es obligatoria')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })

        # Verificar que exista al menos un parámetro
        parametro_keys = [k for k in request.POST.keys() if k.startswith('parametro_')]
        if not parametro_keys:
            messages.error(request, 'Debe agregar al menos un parámetro')
            return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
                'produccion': produccion,
                'parametros_existentes': parametros_existentes,
            })

        try:
            with transaction.atomic():
                prueba = PruebaQuimica.objects.create(
                    nomenclador_prueba=f"{produccion.lote}-{produccion.catalogo_producto.nombre_comercial}",
                    produccion=produccion,
                    fecha_prueba=fecha_prueba,
                    fecha_vencimiento=fecha_vencimiento,
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

                # Mostrar advertencias si las hay
                for adv in advertencias:
                    messages.warning(request, adv)

                messages.success(request, f'Prueba creada con {parametros_procesados} parámetros')
                return redirect('detalle_prueba_quimica', pk=pk)

        except Exception as e:
            messages.error(request, f'Error al crear la prueba: {str(e)}')
            # Log opcional
            # logger.exception("Error en creación de prueba química")

    # GET request
    return render(request, 'produccion/prueba_quimica/crear_prueba_quimica.html', {
        'produccion': produccion,
        'parametros_existentes': parametros_existentes,
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
            prueba.estado = decision_final
            if prueba.estado == 'Aprobada':
                prueba.resultado_final = True
                prueba.produccion.estado = 'Concluida-Satisfactoria'
                prueba.produccion.save()
                # Aquí creo vale de produccion terminada, envío solicitud de entrada a Almacen y envío notificación a Admin
                almacen_destino = get_object_or_404(Almacen, id=almacen_destino_id)
                vale = Vale_Movimiento_Almacen.objects.create(
                    origen = prueba.produccion.planta.nombre,
                    destino = almacen_destino.nombre, # Aquí va el nuevo parametro almacen desde el modal 
                    entrada = False,
                    tipo = 'Producción terminada',
                    estado='confirmado'
                )
                print(vale.origen)
                #Este es el movimiento especifico del producto
                Movimiento_Prod.objects.create(
                    vale=vale,
                    producto_id=prueba.produccion.catalogo_producto.id,
                    cantidad=prueba.produccion.cantidad_real,
                    lote=prueba.produccion.lote
                )    
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
        """ if prueba.resultado_final == False:

            prod_proceso = Produccion.objects.create(
                lote=lote_final,
                catalogo_producto=catalogo_producto_instance,
                prod_result=product,
                cantidad_estimada=Decimal(produccion_data['cantidad_estimada']),
                costo=prueba.produccion.costo,#Decimal(produccion_data['costo']),                
                planta=prueba.produccion.planta,
                estado='Planificada'
            ) """
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
        return JsonResponse({
            'success': False,
            'message': f'Error al concluir la prueba: {str(e)}'
        }, status=500)    
    """ except Exception as e:
        messages.error(request, f'Error al concluir la prueba: {str(e)}')
        return render(request, 'produccion/prueba_quimica/detalle_prueba_quimica.html', {
            'prueba': prueba,
            'parametros': prueba.detalles.all(),
            'error': True
        }) """

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