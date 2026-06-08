from django.forms import formset_factory
from .forms import RecepcionMateriaPrimaForm, MovimientoFormUpdate
from adquisiciones.models import Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo, DetallesAdquisicionProducto
from inventario.models import Inv_Mat_Prima, Inv_Insumos, Inv_Envase, Inv_Producto 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .movimientos import export_vale                               
import decimal
from django.contrib.auth.models import Group
from utils.models import Notification
from adquisiciones.models import Adquisicion
from envase_embalaje.formato.models import Formato
from produccion.models import Prod_Inv_MP, Produccion, Prod_Inv_Producto
from produccion.envasado.models import DetalleEnvasado, ConsumoInsumoEnvasado, SolicitudEnvasado
from django.views.generic import CreateView, UpdateView, DetailView
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
import json
from .models import (
    Vale_Movimiento_Almacen, Movimiento_MP, Movimiento_Prod,
    Movimiento_EE, Movimiento_Ins, Almacen,
    MateriaPrima, Producto, EnvaseEmbalaje, Insu
)
from usuario.models import CustomUser

class CrearSalidaView(CreateView):
    model = Vale_Movimiento_Almacen
    template_name = 'movimientos/crear_salida.html'
    fields = [
        'almacen', 'tipo',
        'descripcion', 'transportista', 'transportista_cI',
        'chapa', 'recibido_por', 'autorizado_por'
    ]
    success_url = reverse_lazy('movimiento_update')  # Ajusta según tu URL
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Personalizar los campos
        form.fields['almacen'].queryset = Almacen.objects.all()
        form.fields['almacen'].empty_label = "--------- Seleccione un almacén ---------"
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filtrar tipos que son salidas
        tipos_salida = [
            ('Entrega', 'Entrega'),
            ('Transferencia', 'Transferencia'),
            ('Venta', 'Venta'),
            ('Consumo interno', 'Consumo interno'),
            ('I+D', 'I+D'),
            ('No conforme','No conforme'),
            ('Conduce', 'Conduce'),
        ]
        context['tipos_salida'] = tipos_salida
        context['almacenes'] = Almacen.objects.all()
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Crear el vale de movimiento
                vale = form.save(commit=False)
                vale.entrada = False  # Es una salida
                vale.estado = 'borrador'
                vale.autorizado_por = self.request.user.first_name
                destino = self.request.POST.get('destino')
                vale.destino = destino
                almacen_id = self.request.POST.get('almacen')
                almacen = Almacen.objects.filter(id=almacen_id)[0]
                vale.origen = almacen.nombre
                
                # Procesar el carrito desde el formulario
                carrito_data = self.request.POST.get('carrito_data')
                if not carrito_data or carrito_data == '[]':
                    messages.error(self.request, 'Debe agregar al menos un item a la salida')
                    return self.form_invalid(form)
                
                # Parsear el carrito
                carrito = json.loads(carrito_data)
                # Guardar el vale primero para tener un ID
                vale.save()
                # Crear los movimientos para cada item del carrito
                for item in carrito:
                    self.crear_movimiento_item(vale, item)

                # Limpiar el carrito de la sesión si existe
                if 'carrito_salida' in self.request.session:
                    del self.request.session['carrito_salida']
                
                messages.success(
                    self.request, 
                    f'Salida creada exitosamente. Vale #{vale.consecutivo}'
                )
                
                # Redirigir al detalle del vale creado
                return redirect('movimiento_update', pk=vale.id)
                
        except json.JSONDecodeError:
            messages.error(self.request, 'Error al procesar los datos del carrito')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error al crear la salida: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Manejar formulario inválido manteniendo el carrito"""
        messages.error(self.request, 'Por favor corrija los errores en el formulario')
        return super().form_invalid(form)
    
    def crear_movimiento_item(self, vale, item_data):
        """Crea un movimiento específico según el tipo de item"""
        tipo = item_data['tipo']
        cantidad = item_data['cantidad']
        try:
            if tipo == 'materia_prima':
                inv = get_object_or_404(Inv_Mat_Prima, id=item_data['item_id'])
                id = item_data['item_id']                
                if not inv:
                    messages('Error', 'No existe esa materia prima en inventario')
                    raise ValueError(f'Inventario no existe: {id}')
                
                inv_cantidad = inv.cantidad - decimal.Decimal(cantidad)
                Movimiento_MP.objects.create(
                    vale=vale,
                    materia_prima_id=item_data['item_id'],
                    cantidad=cantidad,
                    cantidad_inventario = inv_cantidad,
                    lote=item_data.get('lote', '')
                )
            elif tipo == 'producto':
                inv = get_object_or_404(Inv_Producto, id=item_data['item_id'])
                id = item_data['item_id']                
                if not inv:
                    messages('Error', 'No existe ese producto en inventario')
                    raise ValueError(f'Inventario no existe: {id}')
                
                inv_cantidad = inv.cantidad - decimal.Decimal(cantidad)
                Movimiento_Prod.objects.create(
                    vale=vale,
                    producto_id=item_data['item_id'],
                    cantidad=cantidad,
                    cantidad_inventario = inv_cantidad,
                    lote=item_data.get('lote', '')
                )
            elif tipo == 'envase':
                ee = EnvaseEmbalaje.objects.get_or_create(
                        id=item_data['item_id'])[0]
                inv = get_object_or_404(Inv_Envase, envase=item_data['item_id'])
                id = item_data['item_id']                
                if not inv:
                    messages('Error', 'No existe ese envase en inventario')
                    raise ValueError(f'Inventario no existe: {id}')
                inv_cantidad = inv.cantidad - cantidad
                Movimiento_EE.objects.create(
                    vale=vale,
                    envase_embalaje=ee,
                    cantidad=cantidad,
                    cantidad_inventario = inv_cantidad,
                    lote=item_data.get('lote', '')
                )
            elif tipo == 'insumo':
                ins = Insu.objects.get_or_create(
                        id=item_data['item_id'])[0]
                inv = get_object_or_404(Inv_Insumos, insumos=item_data['item_id'], almacen=vale.almacen)
                id = item_data['item_id']                
                if not inv:
                    messages('Error', 'No existe ese insumo en inventario')
                    raise ValueError(f'Inventario no existe: {id}')
                inv_cantidad = inv.cantidad - cantidad
                Movimiento_Ins.objects.create(
                    vale=vale,
                    insumo=ins,
                    cantidad=cantidad,
                    cantidad_inventario = inv_cantidad,
                    lote=item_data.get('lote', '')
                )
            else:
                raise ValueError(f'Tipo de item no reconocido: {tipo}')
                
        except Exception as e:
            # Loggear el error
            print(f"Error al crear movimiento para item {item_data}: {e}")
            raise

@require_GET
def buscar_items_almacen(request):
    """Buscar items disponibles en un almacén específico"""
    almacen_id = request.GET.get('almacen_id')
    tipo = request.GET.get('tipo', '')
    term = request.GET.get('q', '')
    
    print(f"Busqueda: almacen_id={almacen_id}, tipo={tipo}, term={term}")
    
    items = []
        
    if tipo == 'materia_prima' or not tipo:
        from inventario.models import Inv_Mat_Prima  
        
        query = Inv_Mat_Prima.objects.filter(
            almacen_id=almacen_id,
            cantidad__gt=0
        )
        
        if term:
            query = query.filter(
                Q(materia_prima__nombre__icontains=term) |
                Q(materia_prima__codigo__icontains=term)
            )
        
        items.extend([{
            'id': item.id,
            'tipo': 'materia_prima',
            'nombre': item.materia_prima.nombre,
            'codigo': item.materia_prima.codigo,
            'cantidad_disponible': float(item.cantidad),
            'unidad': getattr(item.materia_prima, 'unidad_medida', ''),
            'lote': ''
        } for item in query[:50]])  # Limitar resultados

    if tipo == 'producto' or not tipo:
        from inventario.models import Inv_Producto  # Ajusta según tu app
        
        query = Inv_Producto.objects.filter(
            almacen_id=almacen_id,
            cantidad__gt=0
        )
        
        
        if term:
            query = query.filter(
                Q(producto__nombre_comercial__icontains=term) |
                Q(producto__codigo_producto__icontains=term)
            )
        
        items.extend([{
            'id': item.id,
            'tipo': 'producto',
            'nombre': item.producto.nombre_comercial,
            'codigo': item.producto.codigo_producto,
            'cantidad_disponible': float(item.cantidad),
            'unidad': getattr(str(item.formato), 'formato', ''),
            'lote': item.lote
        } for item in query[:50]])  # Limitar resultados

        

    if tipo == 'envase' or not tipo:
        from inventario.models import Inv_Envase  # Ajusta según tu app
        
        query = Inv_Envase.objects.filter(
            almacen_id=almacen_id,
            cantidad__gt=0
        )
        
        if term:
            query = query.filter(
                envase__tipo_envase_embalaje__nombre__icontains=term
            )

        items.extend([{
            'id': item.envase.id,
            'tipo': 'envase', #item.envase.tipo_envase_embalaje.nombre,
            'nombre': item.envase.tipo_envase_embalaje.nombre + ' ' + item.envase.nombre,
            'codigo': item.envase.codigo_envase,
            'cantidad_disponible': float(item.cantidad),
            'unidad': getattr(str(item.envase), 'formato', ''),
            'lote': ''
        } for item in query[:50]])  # Limitar resultados

    if tipo == 'insumo' or not tipo:
        from inventario.models import Inv_Insumos  # Ajusta según tu app
        
        query = Inv_Insumos.objects.filter(
            almacen_id=almacen_id,
            cantidad__gt=0
        )
        
        if term:
            query = query.filter(
                Q(insumos__nombre__icontains=term) |
                Q(insumos__codigo__icontains=term)
            )
        
        items.extend([{
            'id': item.insumos.id,
            'tipo': 'insumo',
            'nombre': item.insumos.nombre,
            'codigo': item.insumos.codigo,
            'cantidad_disponible': float(item.cantidad),
            'unidad': getattr(item.insumos, 'formato', ''),
            'lote': ''
        } for item in query[:50]])  # Limitar resultados

    return JsonResponse({'items': items})

def reducir_inventario(vale, inv, cantidad):
    if vale.tipo == 'Materias primas':
        inventario_mp = get_object_or_404(Inv_Mat_Prima,
                    materia_prima=inv.id, almacen=inv.almacen)
        inventario_mp.cantidad = inventario_mp.cantidad - cantidad
        inventario_mp.save()
        Movimiento_MP.objects.create(
                vale=vale,
                materia_prima_id=inv.id,
                cantidad=cantidad,
                cantidad_inventario = inventario_mp.cantidad
        )
             
    elif vale.tipo == 'Productos':
        inventario_prod = get_object_or_404(Inv_Producto,
                    producto=inv.id, almacen=inv.almacen)
        inventario_prod.cantidad = inventario_prod.cantidad - cantidad
        inventario_prod.save()
        Movimiento_Prod.objects.create(
                vale=vale,
                producto_id=inv.id,
                cantidad=cantidad,
                cantidad_inventario = inventario_prod.cantidad,
                lote=inv.lote
        )

    elif vale.tipo == 'Envases y embalajes':
        inventario_env = get_object_or_404(Inv_Envase,
                    envase=inv.id, almacen=inv.almacen)
        inventario_env.cantidad = inventario_env.cantidad - cantidad
        inventario_env.save()
        Movimiento_EE.objects.create(
                vale=vale,
                envase_embalaje_id=inv.id,
                cantidad=cantidad,
                cantidad_inventario = inventario_env.cantidad
        )

    elif vale.tipo == 'Insumos':
        inventario_ins = get_object_or_404(Inv_Insumos,
                    insumos=inv.id, almacen=inv.almacen)
        inventario_ins.cantidad = inventario_ins.cantidad - cantidad
        inventario_ins.save()
        Movimiento_Ins.objects.create(
                vale=vale,
                insumo_id=inv.id,
                cantidad=cantidad,
                cantidad_inventario = inventario_ins.cantidad
        )

def validar_disponibilidad_env(movimiento, almacen):
    """Validar disponibilidad de materia prima"""
    from inventario.models import Inv_Envase
    
    inventario = Inv_Envase.objects.filter(
        envase=movimiento.envase,
        almacen=almacen
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.envase.nombre}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )

def validar_disponibilidad_ins(movimiento, almacen):
    """Validar disponibilidad de insumo"""
    from inventario.models import Inv_Insumos
    
    inventario = Inv_Insumos.objects.filter(
        insumos=movimiento.insumos,
        almacen=almacen
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.insumos.nombre}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )
        
class DetalleValeView(DetailView):
    """Vista para ver el detalle de un vale"""
    model = Vale_Movimiento_Almacen
    template_name = 'inventario/salida/detalle_vale.html'
    context_object_name = 'vale'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agrupar movimientos por tipo
        context['materias_primas'] = self.object.movimientos.all()
        context['productos'] = self.object.movimientos_productos.all()
        context['envases'] = self.object.movimientos_envases.all()
        context['insumos'] = self.object.movimientos_insumos.all()
        
        return context

def salida_produccion(request, vale_id):
    mp_prod = Prod_Inv_MP.objects.filter(vale__id=vale_id, vale__estado='confirmado', vale__tipo = 'Solicitud')
    prod_prod = Prod_Inv_Producto.objects.filter(vale__id=vale_id, vale__estado='confirmado', vale__tipo = 'Solicitud')
    if mp_prod:
        produccion = get_object_or_404(Produccion, lote=mp_prod[0].lote_prod.lote)
        almacen = mp_prod[0].almacen
    elif prod_prod:
        produccion = get_object_or_404(Produccion, lote=prod_prod[0].lote_prod.lote)
        almacen = prod_prod[0].almacen
    #if produccion.estado == 'Planificada':
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = almacen.nombre,
                destino = produccion.planta.nombre,
                entrada = False,
                tipo = 'Entrega',
                lote_No = produccion.lote,
                estado='confirmado'
        )
        # Procesar cada mp
        vale_s = None
        if mp_prod:
            for mp in mp_prod:
                if not vale_s:
                    vale_s = mp.vale
                try:
                    field_name = str(mp.inv_materia_prima.id)
                    cantidad = decimal.Decimal('0.000')
                    cantidad = decimal.Decimal(float(request.POST.get(field_name))) 
                    canr_float = float(request.POST.get(field_name))
                    mp.inv_materia_prima.cantidad = mp.inv_materia_prima.cantidad - cantidad
                    mp.inv_materia_prima.save()
                    Movimiento_MP.objects.create(
                        materia_prima=mp.inv_materia_prima,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad,
                        cantidad_inventario = mp.inv_materia_prima.cantidad                        
                    )
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass
                mp.vale.estado = 'despachado'
                mp.vale.save()
        if prod_prod:
            
            for p in prod_prod:
                if not vale_s:
                    vale_s = p.vale
                try:
                    field_name = str(p.producto.id)
                    cantidad = decimal.Decimal('0.000')
                    cantidad = decimal.Decimal(float(request.POST.get(field_name)))                    
                    p.producto.cantidad = p.producto.cantidad - cantidad
                    p.producto.save()
                    Movimiento_Prod.objects.create(
                        producto=p.producto,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad,
                        cantidad_inventario = p.producto.cantidad                        
                    )
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error MovInv...{e}")
                    pass
                p.vale.estado = 'despachado'
                p.vale.save()    
        vale_s.estado = 'despachado'
        vale_s.save()
        return redirect('movimiento_list')  # Redirigir a página de éxito                               
    """ else:
        messages.info(request, 'La producción no está en estado Planificada') """    
    if mp_prod:
        return render(request, 'movimientos/salida_mp.html', {
            'materias_primas': mp_prod, 'produccion': produccion
        })
    else:
        return render(request, 'movimientos/salida_prod.html', {
            'productos': prod_prod, 'produccion': produccion
        })

def salida_envasado(request, vale_id):
    vale_solicitud = get_object_or_404(Vale_Movimiento_Almacen, id=vale_id)
    env_env = DetalleEnvasado.objects.filter(vale__id=vale_id, vale__estado='confirmado', vale__tipo = 'Solicitud envasado')
    ins_env = ConsumoInsumoEnvasado.objects.filter(vale__id=vale_id, vale__estado='confirmado', vale__tipo = 'Solicitud envasado')
    producto = env_env[0].solicitud.lote_produccion_origen
    almacen = env_env[0].solicitud.lote_produccion_origen.almacen
    cant_prod = env_env[0].solicitud.cantidad_solicitada
    if request.method == 'POST':        
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = almacen.nombre,
                destino = 'Envasado',
                entrada = False,
                tipo = 'Salida a envasado',
                lote_No = producto.lote,
                estado='confirmado'
        )
        field_name = str(producto.id)
        cantidad = decimal.Decimal('0.000')
        cantidad = decimal.Decimal(float(request.POST.get(field_name)))
        # Procesar producto
        producto.cantidad = producto.cantidad - cantidad
        producto.save()
        Movimiento_Prod.objects.create(
                        producto=producto,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad,
                        cantidad_inventario = producto.cantidad                        
                    )
        # Procesar cada envase
        
        if env_env:
            for env in env_env:
                try:
                    field_name = str(env.presentacion.id)
                    cantidad = decimal.Decimal('0.00')
                    cantidad = decimal.Decimal(float(request.POST.get(field_name)))
                    env.presentacion.cantidad = env.presentacion.cantidad - cantidad
                    env.presentacion.save()
                    Movimiento_EE.objects.create(
                        envase_embalaje=env.presentacion.envase,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad,
                        cantidad_inventario = env.presentacion.cantidad                        
                    )

                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass
        if ins_env:
            for ins in ins_env:
                try:
                    field_name = str(ins.insumo.id)
                    cantidad = decimal.Decimal('0.00')
                    cantidad = decimal.Decimal(float(request.POST.get(field_name)))
                    ins.insumo.cantidad = ins.insumo.cantidad - cantidad
                    ins.insumo.save()
                    Movimiento_Ins.objects.create(
                        insumo=ins.insumo.insumos,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad,
                        cantidad_inventario = ins.insumo.cantidad                      
                    )
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass
        vale_solicitud.estado = 'despachado'
        vale_solicitud.save()
        
        return redirect('movimiento_list')  # Redirigir a página de éxito                               
      
    return render(request, 'movimientos/salida_env.html', {
            'envases': env_env, 'insumos': ins_env, 'producto': producto, 'cant_prod': cant_prod
        })
    
def recepcion_materia_prima(request, adq_id):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_mat = DetallesAdquisicion.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    if request.method == 'POST':
        for inv in inv_mat:
            field_name = str(inv.materia_prima.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = round(float(request.POST.get(field_name)), 2)
            cantidad = decimal.Decimal(cantidad)
            if not cantidad:
                messages.info(request, 'Debe especificar la cantidad de todas las materias primas')
                return redirect('recepcion_env', adq_id=adq_id)
        
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = 'Adquisición',
                destino = almacen.nombre,
                entrada = True,
                tipo = 'Adquisición'
            )
        
        # Procesar cada producto
        for inv in inv_mat:
            field_name = str(inv.materia_prima.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = round(float(request.POST.get(field_name)), 2)
            cantidad = decimal.Decimal(cantidad)
            try:
                    inventario_mp, created = Inv_Mat_Prima.objects.get_or_create(
                        materia_prima=inv.materia_prima, almacen=almacen)
                    if created:
                        inventario_mp.cantidad = cantidad
                        inventario_mp.save()
                    else:
                        inventario_mp.cantidad = inventario_mp.cantidad + cantidad
                        inventario_mp.save()
                    Movimiento_MP.objects.create(
                        materia_prima=inventario_mp,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_mp.cantidad                        
                    )

                    inv.cantidad_recibida = cantidad
                    inv.save()  
                               
                    if not cantidad == inv.cantidad:
                        target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                        # Crear notificaciones para cada usuario en ese grupo
                        for group in target_groups:
                            for user in group.customuser_set.all():
                                # Notificación en base de datos
                                Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la recepción con la adquisición de: {inv.materia_prima.nombre}. Cantidad adquirida: {inv.cantidad}, Cantidad recibida: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                                )                    
            except Exception as e: #(ValueError, TypeError):
                    messages.error(request, 'Error al actualizar los inventarios')

        adquisicion.registrada = True
        adquisicion.estado = 'completado'
        adquisicion.save()
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_mp.html', {
        'productos': inv_mat, 'adquisicion': adquisicion
    })

def recepcion_producto(request, adq_id):
    # Líneas de la adquisición
    detalles = DetallesAdquisicionProducto.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        return redirect('producto_list')

    almacen = adquisicion.almacen
    
    if request.method == 'POST':
        for detalle in detalles:
            # 1. Formato seleccionado
            formato_id = request.POST.get(f'formato_{detalle.id}')
            # 2. Cantidad ingresada
            cantidad_str = request.POST.get(f'quantity_{detalle.id}', '0')
             # 3. Lote (NUEVO)
            lote = request.POST.get(f'lote_{detalle.id}', '').strip()

            if not lote:
                errores.append(f"{detalle.producto.nombre_comercial}: Número de lote obligatorio")
                return redirect('recepcion_producto', adq_id=adq_id)
            
            try:
                cantidad = round(float(cantidad_str), 2)
                cantidad = decimal.Decimal(cantidad)
            except (ValueError, TypeError):
                cantidad = decimal.Decimal('0.00')

            try:
                formato = Formato.objects.get(id=formato_id)
            except Formato.DoesNotExist:
                messages.error(request, 'No existe ese formato')
                return redirect('recepcion_producto', adq_id=adq_id)

            if not (cantidad and formato_id):
                messages.info(request, 'Falta la cantidad o formato') 
                return redirect('recepcion_producto', adq_id=adq_id)
            

        vale = Vale_Movimiento_Almacen.objects.create(
            almacen=almacen,
            destino=almacen.nombre,
            origen='Adquisición',
            entrada=True,
            tipo='Adquisición',
            estado='confirmado'
        )

        errores = []
        for detalle in detalles:
            formato_id = request.POST.get(f'formato_{detalle.id}')
            cantidad_str = request.POST.get(f'quantity_{detalle.id}', '0')
            lote = request.POST.get(f'lote_{detalle.id}', '').strip()
            cantidad = round(float(cantidad_str), 2)
            cantidad = decimal.Decimal(cantidad)
            formato = Formato.objects.get(id=formato_id)
            # Buscar o crear el inventario para este producto + almacén + formato
            inventario_prod, creado = Inv_Producto.objects.get_or_create(
                producto=detalle.producto,
                almacen=almacen,
                formato=formato,
                lote=lote
            )

            # Sumar cantidad
            inventario_prod.cantidad = inventario_prod.cantidad + cantidad
            inventario_prod.save()

            detalle.cantidad_recibida = cantidad
            detalle.save()
            
            # Registrar movimiento
            Movimiento_Prod.objects.create(
                producto=inventario_prod,
                vale=vale,
                cantidad=cantidad,
                cantidad_inventario=inventario_prod.cantidad
            )

            # Notificar si la cantidad recibida difiere de la adquirida
            if cantidad != detalle.cantidad:
                target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                for group in target_groups:
                    for user in group.customuser_set.all():
                        Notification.objects.create(
                            user=user,
                            message=(
                                f"No coincide la recepción con la adquisición de: "
                                f"{detalle.producto.nombre_comercial} "
                                f"({formato}). "
                                f"Cantidad adquirida: {detalle.cantidad}, "
                                f"Cantidad recibida: {cantidad}"
                            ),
                            link='/movimientos/lista/'
                        )
        # Si hay errores, mostrar mensajes y no completar la recepción
        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect('recepcion_producto', adq_id=adq_id)
        
        adquisicion.registrada = True
        adquisicion.estado = 'completado'
        adquisicion.save()

        messages.success(request, "Recepción completada exitosamente")
        return redirect('producto_list')

    # --- GET: preparar datos para el template ---
    formatos = Formato.objects.all()
    productos_data = []
    for detalle in detalles:
        productos_data.append({
            'detalle': detalle,
            'formatos': [(f.id, str(f)) for f in formatos],
        })

    return render(request, 'movimientos/recepcion_prod.html', {
        'productos_data': productos_data,
        'adquisicion': adquisicion,
    })

def recepcion_envase(request, adq_id):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_env = DetallesAdquisicionEnvase.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    if request.method == 'POST':
        print('En recepcion envase')
        # Procesar cada producto
        for inv in inv_env:
            field_name = str(inv.envase_embalaje.codigo_envase)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if not cantidad:
                messages.info(request, 'Debe especificar la cantidad')
                return redirect('recepcion_env', adq_id=adq_id)

        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                destino = almacen.nombre,
                entrada=True,
                tipo = 'Adquisición'
        )

        for inv in inv_env:
            field_name = str(inv.envase_embalaje.codigo_envase)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            try:
                inventario_ev, created = Inv_Envase.objects.get_or_create(
                envase=inv.envase_embalaje, almacen=almacen)
                if created:
                    inventario_ev.cantidad = cantidad
                    inventario_ev.save()
                else:
                    inventario_ev.cantidad = inventario_ev.cantidad + cantidad
                    inventario_ev.save()
            except Exception as e: #(ValueError, TypeError):
                    messages.error(request, 'Ocurrió algún error al actualizar el inventario')
                    return redirect('recepcion_env', adq_id=adq_id)
            
            Movimiento_EE.objects.create(
                        envase_embalaje=inv.envase_embalaje,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_ev.cantidad
            )
            
            if not cantidad == inv.cantidad:
                target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                # Crear notificaciones para cada usuario en ese grupo
                for group in target_groups:
                    for user in group.customuser_set.all():
                        # Notificación en base de datos
                        Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la recepción con la adquisición de: {inv.envase_embalaje.codigo_envase}. Cantidad adquirida: {inv.cantidad}, Cantidad recibida: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                        )

            inv.cantidad_recibida = cantidad                    
            inv.save()
                    
        adquisicion.registrada = True
        adquisicion.estado = 'completado'
        adquisicion.save()
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito

    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_env.html', {
        'productos': inv_env
    })

def recepcion_insumo(request, adq_id):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_ins = DetallesAdquisicionInsumo.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        return redirect('insumos_list')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    #tipo = Vale_Movimiento_Almacen.VALE_TYPES['recepcion']
    if request.method == 'POST':
        for inv in inv_ins:
            field_name = str(inv.insumo.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if not cantidad:
                messages.info(request, 'Debe especificar la cantidad de cada insumo')
                return redirect('recepcion_ins', adq_id=adq_id)

        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                destino = almacen.nombre,
                entrada=True,
                tipo = 'Adquisición'
            )
        
        for inv in inv_ins:
            field_name = str(inv.insumo.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            try:
                inventario_in, created = Inv_Insumos.objects.get_or_create(
                    insumos=inv.insumo, almacen=almacen)
                if created:
                    inventario_in.cantidad = cantidad
                    inventario_in.save()
                else:
                    inventario_in.cantidad = inventario_in.cantidad + cantidad
                    inventario_in.save()
            except Exception as e: #(ValueError, TypeError):
                messages.error(request, 'Error al actualizar el inventario') 
                return redirect('recepcion_ins', adq_id=adq_id)
           
            Movimiento_Ins.objects.create(
                        insumo=inv.insumo,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_in.cantidad
            )

            if not cantidad == inv.cantidad:
                target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                # Crear notificaciones para cada usuario en ese grupo
                for group in target_groups:
                    for user in group.customuser_set.all():
                        # Notificación en base de datos
                        Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la recepción con la adquisición de: {inv.insumo.nombre}. Cantidad adquirida: {inv.cantidad}, Cantidad recibida: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                        )

            inv.cantidad_recibida = cantidad
            inv.save()
        adquisicion.registrada = True
        adquisicion.estado = 'completado'
        adquisicion.save()
        return redirect('insumos_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_ins.html', {
        'productos': inv_ins
    })

def entrada_materia_prima(request, pk):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    vale_v = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    if vale_v.estado == 'recibido':
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito        
    almacen = Almacen.objects.filter(nombre=vale_v.destino)[0] 
    inv_mat = vale_v.movimientos.all()
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = vale_v.almacen.nombre,
                destino = almacen.nombre,
                entrada = True,
                tipo = 'Entrada',
                estado = 'confirmado'
            )
        # Procesar cada producto que viene del vale de salida
        for inv in inv_mat:
            field_name = str(inv.materia_prima.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = round(float(request.POST.get(field_name)), 2)
            cantidad = decimal.Decimal(cantidad)
            if cantidad:
                try:
                    inventario_mp, created = Inv_Mat_Prima.objects.get_or_create(
                        materia_prima=inv.materia_prima.materia_prima, almacen=almacen)
                    if created:
                        inventario_mp.cantidad = cantidad
                        inventario_mp.save()
                    else:
                        inventario_mp.cantidad = inventario_mp.cantidad + cantidad
                        inventario_mp.save()
                    
                    Movimiento_MP.objects.create(
                        materia_prima=inventario_mp,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_mp.cantidad                        
                    )
                    if not cantidad == inv.cantidad:
                        target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                        # Crear notificaciones para cada usuario en ese grupo
                        for group in target_groups:
                            for user in group.customuser_set.all():
                                # Notificación en base de datos
                                Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la entrada con lo enviado de: {inv.materia_prima.materia_prima.nombre}. Cantidad enviada: {inv.cantidad}, Cantidad entrada: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                                )                    
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass
            else:
                print("No encontro cantidad")
        vale_v.estado = 'recibido'
        vale_v.save()
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/entrada_mp.html', {
        'inv_mp': inv_mat, 'vale': vale_v
    })

def entrada_envase(request, pk):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    vale_v = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    if vale_v.estado == 'recibido':
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito        
    almacen = Almacen.objects.filter(nombre=vale_v.destino)[0] 
    inv_env = vale_v.movimientos_envases.all()
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = vale_v.almacen.nombre,
                destino = almacen.nombre,
                entrada=True,
                tipo = 'Entrada',
                estado = 'confirmado'
            )
        # Procesar cada producto
        for inv in inv_env:
            field_name = str(inv.envase_embalaje.codigo_envase)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if cantidad:
                try:
                    inventario_ev, created = Inv_Envase.objects.get_or_create(
                        envase=inv.envase_embalaje, almacen=almacen)
                    if created:
                        inventario_ev.cantidad = cantidad
                        inventario_ev.save()
                    else:
                        inventario_ev.cantidad = inventario_ev.cantidad + cantidad
                        inventario_ev.save()
                    Movimiento_EE.objects.create(
                        envase_embalaje=inv.envase_embalaje,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_ev.cantidad
                    )
                    if not cantidad == inv.cantidad:
                        target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                        # Crear notificaciones para cada usuario en ese grupo
                        for group in target_groups:
                            for user in group.customuser_set.all():
                                # Notificación en base de datos
                                Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la entrada con el envío de: {inv.envase_embalaje.codigo_envase}. Cantidad enviada: {inv.cantidad}, Cantidad recibida: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                                )
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No se encontro cantidad")
        vale_v.estado = 'recibido'
        vale_v.save()
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito

    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/entrada_env.html', {
        'inv_env': inv_env, 'vale': vale_v
    })

def entrada_insumo(request, pk):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    vale_v = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    if vale_v.estado == 'recibido':
        return redirect('insumos_list')  # Redirigir a página de éxito        
    almacen = Almacen.objects.filter(nombre=vale_v.destino)[0] 
    inv_ins = vale_v.movimientos_insumos.all()
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = vale_v.almacen.nombre,
                destino = almacen.nombre,
                entrada=True,
                tipo = 'Entrada', 
                estado = 'confirmado'
            )
        # Procesar cada producto
        for inv in inv_ins:
            field_name = str(inv.insumo.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if cantidad:
                try:
                    inventario_in, created = Inv_Insumos.objects.get_or_create(
                        insumos=inv.insumo, almacen=almacen)
                    if created:
                        inventario_in.cantidad = cantidad
                        inventario_in.save()
                    else:
                        inventario_in.cantidad = inventario_in.cantidad + cantidad
                        inventario_in.save()
                    Movimiento_Ins.objects.create(
                        insumo=inv.insumo,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_in.cantidad
                    )
                    if not cantidad == inv.cantidad:
                        target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                        # Crear notificaciones para cada usuario en ese grupo
                        for group in target_groups:
                            for user in group.customuser_set.all():
                                # Notificación en base de datos
                                Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la recepción con la entrada de: {inv.insumo.nombre}. Cantidad enviada: {inv.cantidad}, Cantidad recibida: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                                )
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No encontró cantidad")
        vale_v.estado = 'recibido'
        vale_v.save()
        return redirect('insumos_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/entrada_ins.html', {
        'inv_ins': inv_ins, 'vale': vale_v
    })

def entrada_producto(request, pk):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    vale_v = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    if vale_v.estado == 'recibido':
        return redirect('producto_list')  # Redirigir a página de éxito
    tipo = 'Entrada'
    origen = vale_v.almacen.nombre if vale_v.almacen else ''
    if vale_v.tipo == 'Producción terminada' or vale_v.tipo == 'Producción rechazada':
        origen = vale_v.origen
    almacen = Almacen.objects.filter(nombre=vale_v.destino)[0] 
    inv_prod = vale_v.movimientos_productos.all()
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = origen,
                destino = almacen.nombre,
                estado = 'confirmado',
                entrada=True,
                tipo = 'Entrada',
                lote_No = vale_v.lote_No
            )
        # Procesar cada producto
        for inv in inv_prod:
            field_name = str(inv.producto.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            cantidad = decimal.Decimal(cantidad)
            if cantidad:
                try:
                    inventario_prod, created = Inv_Producto.objects.get_or_create(
                        lote=inv.producto.lote, producto=inv.producto.producto, almacen=almacen)
                    if created:
                        inventario_prod.cantidad = cantidad
                        inventario_prod.formato = inv.producto.formato
                        inventario_prod.save()
                    else:
                        inventario_prod.cantidad = inventario_prod.cantidad + cantidad
                        inventario_prod.save()
                    
                    Movimiento_Prod.objects.create(
                        producto=inventario_prod,
                        vale=vale,  
                        cantidad=cantidad,
                        cantidad_inventario = inventario_prod.cantidad
                    )
                    if not cantidad == inv.cantidad:
                        target_groups = Group.objects.filter(name__in=["Presidencia-Admin"])
                        # Crear notificaciones para cada usuario en ese grupo
                        for group in target_groups:
                            for user in group.customuser_set.all():
                                # Notificación en base de datos
                                Notification.objects.create(
                                    user=user,
                                    message=f"No coincide la recepción con la adquisición de: {inv.producto.producto.nombre_comercial}. Cantidad adquirida: {inv.cantidad}, Cantidad recibida: {cantidad}",
                                    link=f'/movimientos/lista/'  # Ir a verificar la cantidad de materia prima en inventario 
                                )
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No encontró cantidad")
        vale_v.estado = 'recibido'
        vale_v.save()
        return redirect('producto_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/entrada_prod.html', {
        'productos': inv_prod, 'vale': vale_v
    })

def movimiento_list(request):
    if request.user.groups.filter(name__in=['Almaceneros']):
        almacen = Almacen.objects.filter(responsable=request.user).first()
        if almacen:
            movimientos = Vale_Movimiento_Almacen.objects.filter(almacen=almacen).order_by('consecutivo')
        else:
            messages.info(request, 'No se encontró almacén asociado')
            movimientos = None
    elif request.user.groups.filter(name__in=['Tecnologa']):
        movimientos = Vale_Movimiento_Almacen.objects.filter(tipo__in=['Solicitud', 'Devolución', 'Producción terminada', 'Producción rechazada', 'Solicitud envasado', 'Envasado']).order_by('consecutivo')
    else:
        movimientos = Vale_Movimiento_Almacen.objects.all().order_by('consecutivo')
    return render(request, 'movimientos/movimientos_list.html', {
        'movimientos': movimientos
    })

def recepciones_pendientes_list(request):
    rec_pendientes = None
    mov_pendientes = None
    if request.user.groups.filter(name__in=['Almaceneros']):
        almacen = Almacen.objects.filter(responsable=request.user).first()    
        if almacen:
            rec_pendientes = Adquisicion.objects.filter(registrada=False, almacen=almacen).all()
            mov_pendientes = Vale_Movimiento_Almacen.objects.filter(destino=almacen.nombre, estado='confirmado', tipo__in=['Producción terminada', 'Devolución', 'Envasado', 'Transferencia', 'Producción rechazada'])
        else:
            messages.info(request, 'Usted no tiene asignado ningún almacén')
    else:
        rec_pendientes = Adquisicion.objects.filter(registrada=False).all()
        mov_pendientes = Vale_Movimiento_Almacen.objects.filter(estado='confirmado', tipo__in=['Producción terminada', 'Devolución', 'Envasado', 'Transferencia', 'Producción rechazada'])
    return render(request, 'movimientos/recepciones_list.html', {
        'rec_pendientes': rec_pendientes,
        'mov_pendientes': mov_pendientes
    })

def solicitudes_pendientes_list(request):
    if request.user.groups.filter(name__in=['Almaceneros']):
        almacen = Almacen.objects.filter(responsable=request.user).first()    
        sol_pendientes = Vale_Movimiento_Almacen.objects.filter(
            tipo='Solicitud', despachado=False, estado='confirmado', almacen=almacen
        ).order_by('id')
        sol_ventas =Vale_Movimiento_Almacen.objects.filter(
            tipo='Venta', despachado=False, estado='borrador', almacen=almacen
        ).order_by('id')
        # Solicitudes de envasado (vales)
        vales_envasado = Vale_Movimiento_Almacen.objects.filter(
            tipo='Solicitud envasado', despachado=False, estado='confirmado', almacen=almacen
        ).prefetch_related(
            'env_envasado__solicitud__lote_produccion_origen__producto',
            'env_envasado__presentacion__envase',
            'ins_envasado__insumo__insumos',
        )
    else:        
        sol_pendientes = Vale_Movimiento_Almacen.objects.filter(
            tipo='Solicitud', despachado=False, estado='confirmado'
        ).order_by('id')
        sol_ventas =Vale_Movimiento_Almacen.objects.filter(
            tipo='Venta', despachado=False, estado='borrador'
        ).order_by('id')
        # Solicitudes de envasado (vales)
        vales_envasado = Vale_Movimiento_Almacen.objects.filter(
            tipo='Solicitud envasado', despachado=False, estado='confirmado'
        ).prefetch_related(
            'env_envasado__solicitud__lote_produccion_origen__producto',
            'env_envasado__presentacion__envase',
            'ins_envasado__insumo__insumos',
        )

    # Lista que contendrá todas las filas a mostrar (incluye las normales y las de envasado)
    filas_tabla = []

    # Agregar solicitudes normales (cada vale es una fila)
    for vale in sol_ventas:
        if vale.get_tipo_inventario == 'Materias primas':
            salida = 'salida_mp'
        elif vale.get_tipo_inventario == 'Envases y embalajes':
            salida = 'salida_env'
        elif vale.get_tipo_inventario == 'Insumos':
            salida = 'salida_ins'
        elif vale.get_tipo_inventario == 'Productos':
            salida = 'salida_prod'
        filas_tabla.append({
            'tipo': 'normal',
            'fecha': vale.fecha_movimiento,
            'tipo_solicitud': vale.get_tipo_display(),  # o 'Solicitud' según tu modelo
            'lote': vale.lote_No,
            'almacen': vale.almacen,                       # campo existente
            'cantidad': vale.cantidad_elementos,
            'vale_id': vale.id,
            'url_detalle': 'movimiento_update',
            'url_entregar': 'salida_prod',                       # para normales no hay entrega especial
        })

    for vale in sol_pendientes:
        filas_tabla.append({
            'tipo': 'normal',
            'fecha': vale.fecha_movimiento,
            'tipo_solicitud': vale.get_tipo_display(),  # o 'Solicitud' según tu modelo
            'lote': '',
            'almacen': vale.almacen,                       # campo existente
            'cantidad': vale.cantidad_elementos,
            'vale_id': vale.id,
            'url_detalle': 'movimiento_update',
            'url_entregar': 'salida_prod',                       # para normales no hay entrega especial
        })

    # Procesar cada solicitud de envasado
    for vale in vales_envasado:
        # Obtener la SolicitudEnvasado relacionada (puede venir desde detalle o consumo)
        solicitud_env = None
        detalle_envases = vale.env_envasado.all()
        env_count = 0
        ins_count = 0
        if detalle_envases.exists():
            env_count = detalle_envases.count()
            solicitud_env = detalle_envases.first().solicitud
        consumos = vale.ins_envasado.all()
        if consumos.exists():
            ins_count = consumos.count()
            solicitud_env = consumos.first().solicitud

        if not solicitud_env:
            continue  # consistencia: debería existir

        # --- Fila 1: Producto a envasar ---
        lote_origen = solicitud_env.lote_produccion_origen
        producto_nombre = lote_origen.producto.nombre_comercial
        lote_codigo = lote_origen.lote or lote_origen.id   # ajusta según tu modelo Inv_Producto

        filas_tabla.append({
            'tipo': 'envasado_producto',
            'fecha': vale.fecha_movimiento,   # o solicitud_env.fecha_solicitud
            'tipo_solicitud': 'Producto a envasar',
            'lote': f"{producto_nombre} - Lote {lote_codigo}",
            'almacen': vale.almacen,
            'cantidad': '1/'  + str(solicitud_env.cantidad_solicitada),
            'vale_id': vale.id,
            'url_detalle': 'movimiento_update',  # si tienes vista de detalle
            'url_entregar': 'salida_env',        # acción principal del envasado
        })

        # --- Fila 2: Envases (agrupados todos en una fila) ---
        envases_texto = []
        for det in detalle_envases:
            envase_nombre = det.presentacion.envase.nombre
            cantidad = det.cantidad_unidades
            envases_texto.append(f"{envase_nombre} x{cantidad}")
        envases_resumen = ", ".join(envases_texto) if envases_texto else "Sin envases"

        filas_tabla.append({
            'tipo': 'envasado_envase',
            'fecha': vale.fecha_movimiento,
            'tipo_solicitud': 'Envases requeridos',
            'lote': envases_resumen,
            'almacen': vale.almacen,
            'cantidad': env_count,# sum(det.cantidad_unidades for det in detalle_envases),  # total unidades
            'vale_id': vale.id,
            'url_detalle': 'movimiento_update',
            'url_entregar': None,  # la acción de entregar solo va en el producto
        })

        # --- Fila 3: Insumos (agrupados) ---
        insumos_texto = []
        for cons in vale.ins_envasado.all():
            insumo_nombre = cons.insumo.insumos.nombre
            cantidad = cons.cantidad_unidades
            insumos_texto.append(f"{insumo_nombre} x{cantidad}")
        insumos_resumen = ", ".join(insumos_texto) if insumos_texto else "Sin insumos"

        filas_tabla.append({
            'tipo': 'envasado_insumo',
            'fecha': vale.fecha_movimiento,
            'tipo_solicitud': 'Insumos requeridos',
            'lote': insumos_resumen,
            'almacen': vale.almacen,
            'cantidad': ins_count, # sum(cons.cantidad_unidades for cons in vale.ins_envasado.all()),
            'vale_id': vale.id,
            'url_detalle': 'movimiento_update',
            'url_entregar': None,
        })

    # Ordenar las filas por fecha (opcional)
    filas_tabla.sort(key=lambda x: x['fecha'], reverse=True)

    return render(request, 'movimientos/solicitudes_list.html', {
        'filas_tabla': filas_tabla,
    })

#Este debe llamarse desde los tipos de movimientos: recepciones, salidas a produccion, ventas, ajustes de inventario  
def generar_vale(request, cons):
    return export_vale(request, cons)

def vale_detalle(request, pk):
    vale = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    # Manejar POST si tienes un formulario de actualización
    if request.method == 'POST':
        # Si tienes un formulario para actualizar
        # form = MovimientoFormUpdate(request.POST, instance=vale) 
        # if form.is_valid():
        #     form.save()
        #     messages.success(request, 'Actualizado correctamente')
        #     return redirect('detalle_vale', pk=vale.pk)
        # else:
        #     messages.error(request, f'Error en el formulario: {form.errors}')
        pass
    
    # Determinar qué tipo de items contiene el vale
    #tipo_inventario = None
    activos = []
    
    # Usar los métodos optimizados del modelo
    tipo_inventario = vale.get_tipo_inventario
    
    
    # Obtener todos los items del vale agrupados por tipo
    materias_primas = vale.movimientos.all()
    productos = vale.movimientos_productos.all()
    envases = vale.movimientos_envases.all()
    insumos = vale.movimientos_insumos.all()
    sol_mp_prod = vale.mp_produccion.all()
    sol_prod_prod = vale.productos_produccion.all()
    sol_env_env = vale.env_envasado.all()
    sol_ins_env = vale.ins_envasado.all()
    solicitud = None
    # Preparar datos para la plantilla
    items_agrupados = []
    total_items = 0
    total_cantidad = 0
    
    if materias_primas.exists():
        for mp in materias_primas:
            items_agrupados.append({
                'tipo': 'Materia Prima',
                'nombre': mp.materia_prima.materia_prima.nombre if mp.materia_prima else 'Sin nombre',
                'codigo': mp.materia_prima.codigo if mp.materia_prima and hasattr(mp.materia_prima, 'codigo') else '',
                'cantidad': mp.cantidad,
                'unidad': getattr(mp.materia_prima, 'unidad_medida', '') if mp.materia_prima else '',
                'lote': mp.lote or '',
                'costo': mp.materia_prima.materia_prima.costo,
                'saldo': mp.cantidad_inventario
            })
            total_items += 1
            total_cantidad += float(mp.cantidad)
    
    if productos.exists():
        for prod in productos:
            items_agrupados.append({
                'tipo': 'Producto',
                'nombre': prod.producto.producto.nombre_comercial if prod.producto else 'Sin nombre',
                'codigo': prod.producto.producto.codigo if prod.producto and hasattr(prod.producto, 'codigo') else '',
                'cantidad': prod.cantidad,
                'unidad': getattr(prod.producto, 'unidad_medida', '') if prod.producto else '',
                'lote': prod.producto.lote or '',
                'costo': prod.costo_unitario,
                'saldo': prod.cantidad_inventario
            })
            total_items += 1
            total_cantidad += float(prod.cantidad)
    
    if envases.exists():
        for env in envases:
            items_agrupados.append({
                'tipo': 'Envase/Embalaje',
                'nombre': env.envase_embalaje.codigo_envase if env.envase_embalaje else 'Sin nombre',
                'codigo': env.envase_embalaje.codigo if env.envase_embalaje and hasattr(env.envase_embalaje, 'codigo') else '',
                'cantidad': env.cantidad,
                'unidad': 'unidad',
                'lote': env.lote or '',
                'costo': env.costo_unitario,
                'saldo': env.cantidad_inventario
            })
            total_items += 1
            total_cantidad += float(env.cantidad)
    
    if insumos.exists():
        for ins in insumos:
            items_agrupados.append({
                'tipo': 'Insumo',
                'nombre': ins.insumo.nombre if ins.insumo else 'Sin nombre',
                'codigo': ins.insumo.codigo if ins.insumo and hasattr(ins.insumo, 'codigo') else '',
                'cantidad': ins.cantidad,
                'unidad': getattr(ins.insumo, 'unidad_medida', '') if ins.insumo else '',
                'lote': ins.lote or '',
                'costo': ins.costo_unitario,
                'saldo': ins.cantidad_inventario
            })
            total_items += 1
            total_cantidad += float(ins.cantidad)

    if sol_mp_prod.exists():
        for mp in sol_mp_prod:
            items_agrupados.append({
                'tipo': 'Materia Prima',
                'nombre': mp.inv_materia_prima.materia_prima.nombre if mp.inv_materia_prima else 'Sin nombre',
                'codigo': mp.inv_materia_prima.codigo if mp.inv_materia_prima and hasattr(mp.inv_materia_prima, 'codigo') else '',
                'cantidad': mp.cantidad_materia_prima,
                'unidad': getattr(mp.inv_materia_prima, 'unidad_medida', '') if mp.inv_materia_prima else '',
                'lote': vale.lote_No,
                'costo': mp.inv_materia_prima.materia_prima.costo,
                'saldo': mp.inv_materia_prima.cantidad
            })
            total_items += 1
            total_cantidad += float(mp.cantidad_materia_prima)
        lote_prod = sol_mp_prod.first().lote_prod
        fecha_prod = sol_mp_prod.first().fecha_creacion

    if sol_prod_prod.exists():
        for prod in sol_prod_prod:
            items_agrupados.append({
                'tipo': 'Materia Prima',
                'nombre': prod.producto.producto.nombre_comercial if prod.producto else 'Sin nombre',
                'codigo': prod.producto.codigo if prod.producto and hasattr(prod.producto, 'codigo') else '',
                'cantidad': prod.cantidad_producto,
                'unidad': getattr(prod.producto, 'unidad_medida', '') if prod.producto else '',
                'lote': vale.lote_No,
                'costo': prod.producto.producto.costo,
                'saldo': prod.producto.cantidad
            })
            total_items += 1
            total_cantidad += float(prod.cantidad_producto)
        lote_prod = sol_prod_prod.first().lote_prod
        fecha_prod = sol_prod_prod.first().fecha_creacion

    if sol_env_env.exists():
        solicitud = sol_env_env.first().solicitud
        items_agrupados.append({
                'tipo': 'Producto',
                'nombre': solicitud.lote_produccion_origen.producto.nombre_comercial if solicitud.lote_produccion_origen else 'Sin nombre',
                'codigo': solicitud.lote_produccion_origen.producto.codigo_producto if solicitud.lote_produccion_origen else '',
                'cantidad': solicitud.cantidad_solicitada,
                'unidad': solicitud.lote_produccion_origen.formato.unidad_medida if solicitud.lote_produccion_origen.formato else '',
                'lote': vale.lote_No,
                'costo': solicitud.lote_produccion_origen.producto.costo,
                'saldo': solicitud.lote_produccion_origen.cantidad
            })
        for env in sol_env_env:
            items_agrupados.append({
                'tipo': 'Envase',
                'nombre': env.presentacion.envase.nombre if env.presentacion else 'Sin nombre',
                'codigo': env.presentacion.codigo_envase if env.presentacion and hasattr(env.presentacion, 'codigo') else '',
                'cantidad': env.cantidad_unidades,
                'unidad': getattr(env.presentacion.envase.formato, 'unidad_medida', '') if env.presentacion.envase.formato else '',
                'lote': vale.lote_No,
                'costo': env.presentacion.envase.costo,
                'saldo': env.presentacion.cantidad
            })
            total_items += 1
            total_cantidad += float(env.cantidad_unidades)

    
    if sol_ins_env.exists():
        for ins in sol_ins_env:
            items_agrupados.append({
                'tipo': 'Insumo',
                'nombre': ins.insumo.insumos if ins.insumo else ' ',
                'codigo': ins.insumo.insumos.codigo if ins.insumo and hasattr(ins.insumo.insumos, 'codigo') else '',
                'cantidad': ins.cantidad_unidades,
                'unidad': 'u',# getattr(ins.insumo.envase.formato, 'unidad_medida', '') if env.presentacion.envase.formato else '',
                'lote': vale.lote_No,
                'costo': ins.insumo.insumos.costo,
                'saldo': ins.insumo.cantidad
            })
            total_items += 1
            total_cantidad += float(env.cantidad_unidades)
        solicitud = sol_env_env.first().solicitud
    else:
        print('No hay insumos')
    # Verificar si está relacionado con producción o envasado
    relacion_produccion = None
    relacion_envasado = None
        
    if vale.mp_produccion.exists():
        relacion_produccion = vale.mp_produccion.first()
    if vale.productos_produccion.exists():
        relacion_produccion = vale.productos_produccion.first()

    if vale.env_envasado.exists():
        relacion_envasado = vale.env_envasado.first()
        
    # Calcular totales de valor si hay costos
    valor_total = 0
    for item in items_agrupados:
        if item['costo']:
            valor_total += float(item['cantidad']) * float(item['costo'])
    
    # Determinar estado para mostrar acciones disponibles
    puede_confirmar = vale.estado == 'borrador'  # Solo salidas en borrador
    puede_cancelar = vale.estado in ['borrador', 'confirmado']
    puede_despachar = vale.estado == 'confirmado' and vale.despachado == False
    context = {
        'vale': vale,
        'tipo_inventario': tipo_inventario,
        'items_agrupados': items_agrupados,
        'total_items': total_items,
        'total_cantidad': total_cantidad,
        'valor_total': valor_total,
        'relacion_produccion': relacion_produccion,
        'relacion_envasado': relacion_envasado,
        'materias_primas': materias_primas,
        'productos': productos,
        'envases': envases,
        'insumos': insumos,
        'sol_mp_prod': sol_mp_prod,
        'sol_prod_prod': sol_prod_prod,
        'sol_env_env': sol_env_env,
        'sol_ins_env': sol_ins_env,
        'puede_confirmar': puede_confirmar,
        'puede_cancelar': puede_cancelar,
        'puede_despachar': puede_despachar,
        'solicitud': solicitud,
        # 'form': form,  # Si mantienes el formulario
    }
    
    return render(request, 'movimientos/detalle_vale.html', context)

# Vista para confirmar una salida
def confirmar_salida(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('movimiento_detalle', pk=pk)
    
    vale = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    # Verificar permisos (agregar según tu sistema de permisos)
    # if not request.user.has_perm('inventario.confirmar_salida'):
    #     messages.error(request, 'No tiene permisos para confirmar salidas')
    #     return redirect('detalle_vale', pk=pk)
    
    # Validar que se pueda confirmar
    if vale.estado != 'borrador':
        messages.error(request, 'Solo se pueden confirmar vales en estado borrador')
        return redirect('detalle_vale', pk=pk)
    
    if vale.entrada:
        messages.error(request, 'Solo se pueden confirmar salidas (no entradas)')
        return redirect('detalle_vale', pk=pk)
    
    try:
        # Lógica de confirmación (puedes mover esto a un método del modelo)
        from django.db import transaction
        
        with transaction.atomic():
            # 1. Validar disponibilidad de inventario
            for movimiento in vale.movimientos.all():
                validar_disponibilidad_mp(movimiento, vale.almacen)
            
            for movimiento in vale.movimientos_productos.all():
                validar_disponibilidad_producto(movimiento, vale.almacen)

            for movimiento in vale.movimientos_envases.all():
                validar_disponibilidad_envase(movimiento, vale.almacen)

            for movimiento in vale.movimientos_insumos.all():
                validar_disponibilidad_insumos(movimiento, vale.almacen)

            # 2. Actualizar estado
            if vale.destino:
                vale.estado = 'confirmado'
            else:
                vale.estado = 'despachado'
            vale.despachado_por = request.user.first_name
            try:
                vale.save()
            except Exception as e:
                print(f'Error inesperado: {str(e)}')

            # 3. Lógica para actualizar inventarios
            
            messages.success(request, f'Vale {vale.consecutivo} confirmado exitosamente')
            
    except ValueError as e:
        messages.error(request, f'Error al confirmar: {str(e)}')
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
    
    return redirect('movimiento_list')

# Funciones auxiliares para validación
def validar_disponibilidad_mp(movimiento, almacen):
    """Validar disponibilidad de materia prima"""
    # Ajusta esto según tus modelos de inventario reales
    from inventario.models import Inv_Mat_Prima

    if not movimiento.materia_prima or movimiento.materia_prima.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.materia_prima.materia_prima.nombre}. '
            f'Disponible: {movimiento.materia_prima.cantidad if movimiento.materia_prima else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )
    else:
        movimiento.materia_prima.cantidad -= movimiento.cantidad
        movimiento.materia_prima.save()
        movimiento.cantidad_inventario = movimiento.materia_prima.cantidad
        movimiento.save()

def validar_disponibilidad_producto(movimiento, almacen):
    """Validar disponibilidad de producto"""
    # Ajusta esto según tus modelos de inventario reales
    from inventario.models import Inv_Producto
    
    if not movimiento.producto or movimiento.producto.cantidad < movimiento.cantidad:
        lote_info = f" (Lote: {movimiento.lote})" if movimiento.lote else ""
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.producto.producto.nombre_comercial}{lote_info}. '
            f'Disponible: {movimiento.producto.cantidad if movimiento.producto else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )
    else:
        movimiento.producto.cantidad -= movimiento.cantidad
        movimiento.producto.save()
        movimiento.cantidad_inventario = movimiento.producto.cantidad
        movimiento.save()

def validar_disponibilidad_envase(movimiento, almacen):
    """Validar disponibilidad de envases"""
    from inventario.models import Inv_Envase
    
    inventario = Inv_Envase.objects.filter(
        envase=movimiento.envase_embalaje,
        almacen=almacen
    ).first()

    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.envase_embalaje.tipo_envase_embalaje}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )
    else:
        inventario.cantidad -= movimiento.cantidad
        inventario.save()
        movimiento.cantidad_inventario = inventario.cantidad
        movimiento.save()

def validar_disponibilidad_insumos(movimiento, almacen):
    """Validar disponibilidad de insumos"""
    from inventario.models import Inv_Insumos
    
    inventario = Inv_Insumos.objects.filter(
        insumos=movimiento.insumo,
        almacen=almacen
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.insumos.nombre}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )
    else:
        inventario.cantidad -= movimiento.cantidad
        inventario.save()
        movimiento.cantidad_inventario = inventario.cantidad
        movimiento.save()
        
class UpdateMovimientoView(UpdateView):
    model = Vale_Movimiento_Almacen
    form_class = MovimientoFormUpdate
    template_name = 'movimientos/movimiento_update.html'
    success_url = reverse_lazy('movimientos:movimiento_list')  # Cambia esto al nombre de tu URL

    def form_valid(self, form):
        messages.success(self.request, "Se ha actualizado correctamente el inventario.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.get('instance')
        if instance:
            kwargs['initial'] = {
                #'tipo_materia_prima': instance.tipo_materia_prima.nombre,
                # 'factura_adquisicion': instance.get_factura_adquisicion_name,
                #'ficha_tecnica': instance.get_ficha_tecnica_name,
                #'hoja_seguridad': instance.get_hoja_seguridad_name,
            }
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        # context['factura_adquisicion_nombre'] = basename(obj.factura_adquisicion.name) if obj.factura_adquisicion else ''
        context['ficha_tecnica_nombre'] = ''#basename(obj.ficha_tecnica.name) if obj.ficha_tecnica else ''
        context['hoja_seguridad_nombre'] = ''#basename(obj.hoja_seguridad.name) if obj.hoja_seguridad else ''
        return context

# Vista para obtener el carrito actual (para AJAX)
@require_POST
def obtener_carrito(request):
    """Obtener el carrito actual de la sesión"""
    carrito = request.session.get('carrito_salida', [])
    return JsonResponse({'items': carrito})

@require_POST
def agregar_item_carrito(request):
    """Agregar item al carrito de la sesión"""
    data = json.loads(request.body)
    
    carrito = request.session.get('carrito_salida', [])
    
    # Verificar si ya existe en el carrito
    for item in carrito:
        if (item['tipo'] == data['tipo'] and 
            item['item_id'] == data['item_id'] and
            item.get('lote', '') == data.get('lote', '')):
            return JsonResponse({
                'error': 'El item ya está en el carrito'
            }, status=400)
    
    carrito.append({
        'tipo': data['tipo'],
        'item_id': data['item_id'],
        'nombre': data['nombre'],
        'cantidad': float(data['cantidad']),
        'lote': data.get('lote', ''),
        'cantidad_disponible': float(data['cantidad_disponible']),
        'unidad': data.get('unidad', '')
    })
    
    request.session['carrito_salida'] = carrito
    return JsonResponse({'success': True, 'count': len(carrito)})

@require_POST
def eliminar_item_carrito(request):
    """Eliminar item del carrito"""
    data = json.loads(request.body)
    
    carrito = request.session.get('carrito_salida', [])
    index = data.get('index')
    
    if index is not None and 0 <= index < len(carrito):
        carrito.pop(index)
        request.session['carrito_salida'] = carrito
    
    return JsonResponse({'success': True, 'count': len(carrito)})    