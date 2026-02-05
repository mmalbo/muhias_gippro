from django.forms import formset_factory
from .forms import RecepcionMateriaPrimaForm, MovimientoFormUpdate
from adquisiciones.models import Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo
from inventario.models import Inv_Mat_Prima, Inv_Insumos, Inv_Envase, Inv_Producto 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .movimientos import export_vale                               
import decimal
from django.contrib.auth.models import Group
from utils.models import Notification
from adquisiciones.models import Adquisicion
from produccion.models import Prod_Inv_MP, Produccion
from django.views.generic import CreateView, UpdateView, DetailView
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
import json

from .models import (
    Vale_Movimiento_Almacen, Movimiento_MP, Movimiento_Prod,
    Movimiento_EE, Movimiento_Ins, Almacen,
    MateriaPrima, Producto, EnvaseEmbalaje
)
from usuario.models import CustomUser

class CrearSalidaView(CreateView):
    model = Vale_Movimiento_Almacen
    template_name = 'movimientos/crear_salida.html'
    fields = [
        'almacen', 'tipo', 'destino',
        'descripcion', 'transportista', 'transportista_cI',
        'chapa', 'recibido_por', 'autorizado_por'
    ]
    success_url = reverse_lazy('movimiento_update')  # Ajusta según tu URL
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Personalizar los campos
        form.fields['almacen'].queryset = Almacen.objects.all()
        form.fields['almacen'].empty_label = "--------- Seleccione un almacén ---------"
        form.fields['destino'].queryset = Almacen.objects.all()
        form.fields['destino'].required = False
        form.fields['destino'].empty_label = "--------- Seleccione destino (opcional) ---------"
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filtrar tipos que son salidas
        tipos_salida = [
            ('Entrega', 'Entrega'),
            ('Transferencia', 'Transferencia'),
            ('Venta', 'Venta'),
            ('Consumo interno', 'Consumo interno'),
            ('Desecho', 'Desecho'),
            ('Merma', 'Merma'),
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
                vale.despachado_por = self.request.user
                
                # Procesar el carrito desde el formulario
                carrito_data = self.request.POST.get('carrito_data')
                print(carrito_data)
                if not carrito_data or carrito_data == '[]':
                    messages.error(self.request, 'Debe agregar al menos un item a la salida')
                    return self.form_invalid(form)
                
                # Parsear el carrito
                carrito = json.loads(carrito_data)
                print(carrito)
                # Guardar el vale primero para tener un ID
                vale.save()
                
                # Crear los movimientos para cada item del carrito
                for item in carrito:
                    print(item)
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
        print(f'tipo en crear item: {tipo}')
        try:
            if tipo == 'materia_prima':
                Movimiento_MP.objects.create(
                    vale=vale,
                    materia_prima_id=item_data['item_id'],
                    cantidad=cantidad,
                    lote=item_data.get('lote', '')
                )
                
            elif tipo == 'producto':
                Movimiento_Prod.objects.create(
                    vale=vale,
                    producto_id=item_data['item_id'],
                    cantidad=cantidad,
                    lote=item_data.get('lote', '')
                )
                
            elif tipo == 'envase':
                ee = EnvaseEmbalaje.objects.get_or_create(
                        id=item_data['item_id'])[0]
                print(ee)
                Movimiento_EE.objects.create(
                    vale=vale,
                    envase_embalaje=item_data['item_id'],
                    cantidad=cantidad,
                    lote=item_data.get('lote', '')
                )
                
            elif tipo == 'insumo':
                print(item_data['item_id'])
                Movimiento_Ins.objects.create(
                    vale=vale,
                    insumo_id=item_data['item_id'],
                    cantidad=cantidad,
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
    print(almacen_id)
    print(tipo)
    print(term)
        
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
            'id': item.materia_prima.id,
            'tipo': 'materia_prima',
            'nombre': item.materia_prima.nombre,
            'codigo': item.materia_prima.codigo,
            'cantidad_disponible': float(item.cantidad),
            'unidad': getattr(item.materia_prima, 'unidad_medida', ''),
            'lote': ''
        } for item in query[:50]])  # Limitar resultados

    if tipo == 'producto' or not tipo:
        print('Producto')
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
            
        print(query)
        
        items.extend([{
            'id': item.producto.id,
            'tipo': 'producto',
            'nombre': item.producto.nombre_comercial,
            'codigo': item.producto.codigo_producto,
            'cantidad_disponible': float(item.cantidad),
            'unidad': getattr(str(item.producto.formato), 'formato', ''),
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
            'tipo': 'envase',
            'nombre': '',
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

    print(f'items:{items}')
    return JsonResponse({'items': items})

""" @require_POST
def confirmar_salida(request, pk):
    vale = get_object_or_404(Vale_Movimiento_Almacen, pk=pk)
    print(vale.estado)
    
    if vale.estado != 'borrador':
        messages.error(request, 'Solo se pueden confirmar vales en estado borrador')
        return redirect('movimiento_update', pk=pk)
    
    try:
        with transaction.atomic():
            # Validar disponibilidad
            for movimiento in vale.movimientos.all():
                validar_disponibilidad_mp(movimiento, vale.almacen)
            
            # Confirmar el vale
            vale.estado = 'confirmado'
            vale.despachado = True
            vale.despachado_por = request.user
            vale.save()
            
            # Actualizar inventarios
            reducir_inventario(vale, 0)
            
            messages.success(request, 'Salida confirmada exitosamente')
            
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('movimiento_update', pk=pk)
 """

def reducir_inventario(vale, inv, cantidad):
    if vale.tipo == 'Materias primas':
        Movimiento_MP.objects.create(
                vale=vale,
                materia_prima_id=inv.id,
                cantidad=cantidad
        )
        inventario_mp = get_object_or_404(Inv_Mat_Prima,
                    materia_prima=inv.id, almacen=inv.almacen)
        inventario_mp.cantidad = inventario_mp.cantidad - cantidad
        inventario_mp.save()     
    elif vale.tipo == 'Productos':
        Movimiento_Prod.objects.create(
                vale=vale,
                producto_id=inv.id,
                cantidad=cantidad,
                lote=inv.lote
        )
        inventario_prod = get_object_or_404(Inv_Producto,
                    producto=inv.id, almacen=inv.almacen)
        inventario_prod.cantidad = inventario_prod.cantidad - cantidad
        inventario_prod.save()
    elif vale.tipo == 'Envases y embalajes':
        Movimiento_EE.objects.create(
                vale=vale,
                envase_embalaje_id=inv.id,
                cantidad=cantidad
        )
        inventario_env = get_object_or_404(Inv_Envase,
                    envase=inv.id, almacen=inv.almacen)
        inventario_env.cantidad = inventario_env.cantidad - cantidad
        inventario_env.save()
    elif vale.tipo == 'Insumos':
        Movimiento_Ins.objects.create(
                vale=vale,
                insumo_id=inv.id,
                cantidad=cantidad
        )
        inventario_ins = get_object_or_404(Inv_Insumos,
                    insumos=inv.id, almacen=inv.almacen)
        inventario_ins.cantidad = inventario_ins.cantidad - cantidad
        inventario_ins.save()
    
""" def validar_disponibilidad_mp(movimiento, almacen):
    from inventario.models import Inv_Mat_Prima
    
    inventario = Inv_Mat_Prima.objects.filter(
        materia_prima=movimiento.materia_prima,
        almacen=almacen
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.materia_prima.nombre}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )

def validar_disponibilidad_prod(movimiento, almacen):
    from inventario.models import Inv_Producto
    
    inventario = Inv_Producto.objects.filter(
        producto=movimiento.producto,
        almacen=almacen
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.producto.nombre}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )
 """

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

def salida_produccion(request, prod_id):
    mp_prod = Prod_Inv_MP.objects.filter(lote_prod=prod_id).all()
    produccion = get_object_or_404(Produccion, id=prod_id)
    if produccion.estado == 'Planificada':
        if request.method == 'POST':
            almacen = mp_prod[0].almacen
            vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = almacen.nombre,
                destino = Produccion.planta.nombre,
                entrada = False,
                tipo = 'Entrega'
            )
        # Procesar cada mp
        for mp in mp_prod:
            try:
                field_name = str(mp.inv_materia_prima.id)
                print(field_name)
                cantidad = decimal.Decimal('0.00')
                cantidad = decimal.Decimal(float(request.POST.get(field_name)))
                print(request.POST.get(field_name))
                Movimiento_MP.objects.create(
                        materia_prima=mp.inv_materia_prima,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad                        
                    )
                print(mp.inv_materia_prima.id)
                print(almacen.id)
                inventario_mp = get_object_or_404(Inv_Mat_Prima,
                    materia_prima=mp.inv_materia_prima.id, almacen=almacen.id)
                inventario_mp.cantidad = inventario_mp.cantidad - cantidad
                inventario_mp.save()  
                return redirect('materia_prima:materia_prima_list')
            except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass         
        return render(request, 'movimientos/salida_mp.html', {
        'materias_primas': mp_prod, 'produccion': produccion
        })

def recepcion_materia_prima(request, adq_id):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_mat = DetallesAdquisicion.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                destino = almacen,
                entrada = True,
                tipo = 'Adquisición'
            )
        # Procesar cada producto
        for inv in inv_mat:
            field_name = str(inv.materia_prima.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = round(float(request.POST.get(field_name)), 2)
            cantidad = decimal.Decimal(cantidad)
            if cantidad:
                try:
                    Movimiento_MP.objects.create(
                        materia_prima=inv.materia_prima,
                        vale=vale,  
                        cantidad=cantidad                        
                    )
                    inventario_mp, created = Inv_Mat_Prima.objects.get_or_create(
                        materia_prima=inv.materia_prima, almacen=almacen)
                    if created:
                        inventario_mp.cantidad = cantidad
                        inventario_mp.save()
                    else:
                        inventario_mp.cantidad = inventario_mp.cantidad + cantidad
                        inventario_mp.save()
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
                    print(f"Error...{e}")
                    pass
            else:
                print("No encontro cantidad")
        adquisicion.registrada = True
        adquisicion.save()
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_mp.html', {
        'productos': inv_mat, 'adquisicion': adquisicion
    })

def recepcion_envase(request, adq_id):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_env = DetallesAdquisicionEnvase.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                destino = almacen,
                entrada=True,
                tipo = 'Adquisición'
            )
        # Procesar cada producto
        for inv in inv_env:
            field_name = str(inv.envase_embalaje.codigo_envase)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if cantidad:
                try:
                    Movimiento_EE.objects.create(
                        envase_embalaje=inv.envase_embalaje,
                        vale_e=vale,  
                        cantidad=cantidad
                    )
                    inventario_ev, created = Inv_Envase.objects.get_or_create(
                        envase=inv.envase_embalaje, almacen=almacen)
                    if created:
                        inventario_ev.cantidad = cantidad
                        inventario_ev.save()
                    else:
                        inventario_ev.cantidad = inventario_ev.cantidad + cantidad
                        inventario_ev.save()
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
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No se encontro cantidad")
        adquisicion.registrada = True
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
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                destino = almacen,
                entrada=True,
                tipo = 'Adquisición'
            )
        # Procesar cada producto
        for inv in inv_ins:
            field_name = str(inv.insumo.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if cantidad:
                try:
                    Movimiento_Ins.objects.create(
                        insumo=inv.insumo,
                        vale_e=vale,  
                        cantidad=cantidad
                    )
                    inventario_in, created = Inv_Insumos.objects.get_or_create(
                        insumos=inv.insumo, almacen=almacen)
                    if created:
                        inventario_in.cantidad = cantidad
                        inventario_in.save()
                    else:
                        inventario_in.cantidad = inventario_in.cantidad + cantidad
                        inventario_in.save()
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
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No encontró cantidad")
        adquisicion.registrada = True
        adquisicion.save()
        return redirect('insumos_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_ins.html', {
        'productos': inv_ins
    })

def movimiento_list(request):
    movimientos = Vale_Movimiento_Almacen.objects.all().order_by('-consecutivo')
    print(movimientos)
    return render(request, 'movimientos/movimientos_list.html', {
        'movimientos': movimientos
    })

def recepciones_pendientes_list(request):
    rec_pendientes = Adquisicion.objects.filter(registrada=False).all()
    return render(request, 'movimientos/recepciones_list.html', {
        'rec_pendientes': rec_pendientes
    })

def solicitudes_pendientes_list(request):
    sol_pendientes = Vale_Movimiento_Almacen.objects.filter(tipo='Solicitud', despachado=False).all()
    return render(request, 'movimientos/solicitudes_list.html', {
        'sol_pendientes': sol_pendientes
    })
    
#Este debe llamarse desde los tipos de movimientos: recepciones, salidas a produccion, ventas, ajustes de inventario  
def generar_vale(request, cons):
    return export_vale(request, cons)

""" def vale_detalle(request, pk):
    vale = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    tipo = vale.tipo
    print(vale.tipo)
    if request.method == 'POST':
        form = MovimientoFormUpdate(request.POST, instance=vale) 
        if form.is_valid():
            form.save()
            messages.success(request, 'Actualizado correctamente')
            return redirect('materia_prima:materia_prima_list') 
        else:
            messages.error(request, f'Error en la form: {form.errors}')
            return redirect('materia_prima:materia_prima_list')
    form = MovimientoFormUpdate(instance=vale)
    if vale.tipo == 'Solicitud':
        activos = vale.mp_produccion.all()
        if activos:
            tipo = 'Solicitud'
    elif vale.tipo == 'Recepción':
        activos = vale.movimientos.all()
        activos = Movimiento_MP.objects.filter(vale=vale)
        if activos:
            tipo = 'materias primas'
        else:
            activos = vale.movimientos_e.all()
            if activos:
                tipo = 'envase o embalaje'
            else:
                activos = vale.movimientos_prod.all()
                activos = Movimiento_Prod.objects.filter(vale_e=vale)
                if activos:
                    tipo = 'productos'
                else:
                    activos = vale.movimientos_i.all()
                    if activos:
                        tipo = 'insumos'
    elif vale.tipo == 'Entrega' or vale.tipo == 'Conduce':
        activos = vale.movimientos.all()
        if activos:
            tipo = 'materias primas'
        else:
            activos = vale.movimientos_e.all()
            if activos:
                tipo = 'envase o embalaje'
            else:
                activos = vale.movimientos_prod.all()
                if activos:
                    tipo = 'productos'
                else:
                    activos = vale.movimientos_i.all()
                    if activos:
                        tipo = 'insumos'
    elif vale.tipo == 'Ajuste de inventario':
        activos = vale.movimientos.all()
        if activos:
            tipo = 'materias primas'
        else:
            activos = vale.movimientos_e.all()
            if activos:
                tipo = 'envase o embalaje'
            else:
                activos = vale.movimientos_prod.all()
                if activos:
                    tipo = 'productos'
                else:
                    activos = vale.movimientos_i.all()
                    if activos:
                        tipo = 'insumos'
    context = {
        'activos':activos,
        'tipo':tipo,
        'vale':vale,
        'form':form,
    }

    return render(request, 'movimientos/movimiento_update.html', context) """

def vale_detalle(request, pk):
    vale = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    print(vale)
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
    
    print(f'tipo_inventario afuera: {tipo_inventario}')
    # Obtener todos los items del vale agrupados por tipo
    materias_primas = vale.movimientos.all()
    productos = vale.movimientos_productos.all()
    envases = vale.movimientos_envases.all()
    insumos = vale.movimientos_insumos.all()
    
    # Preparar datos para la plantilla
    items_agrupados = []
    total_items = 0
    total_cantidad = 0
    
    if materias_primas.exists():
        for mp in materias_primas:
            items_agrupados.append({
                'tipo': 'Materia Prima',
                'nombre': mp.materia_prima.nombre if mp.materia_prima else 'Sin nombre',
                'codigo': mp.materia_prima.codigo if mp.materia_prima and hasattr(mp.materia_prima, 'codigo') else '',
                'cantidad': mp.cantidad,
                'unidad': getattr(mp.materia_prima, 'unidad_medida', '') if mp.materia_prima else '',
                'lote': mp.lote or '',
                'costo': mp.costo_unitario
            })
            total_items += 1
            total_cantidad += float(mp.cantidad)
    
    if productos.exists():
        for prod in productos:
            items_agrupados.append({
                'tipo': 'Producto',
                'nombre': prod.producto.nombre_comercial if prod.producto else 'Sin nombre',
                'codigo': prod.producto.codigo if prod.producto and hasattr(prod.producto, 'codigo') else '',
                'cantidad': prod.cantidad,
                'unidad': getattr(prod.producto, 'unidad_medida', '') if prod.producto else '',
                'lote': prod.lote or '',
                'costo': prod.costo_unitario
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
                'costo': env.costo_unitario
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
                'costo': ins.costo_unitario
            })
            total_items += 1
            total_cantidad += float(ins.cantidad)
    
    # Verificar si está relacionado con producción o envasado
    relacion_produccion = None
    relacion_envasado = None
    
    if vale.salidas_produccion.exists():
        relacion_produccion = vale.salidas_produccion.first()
    
    # Nota: Si mantienes el nombre original de la relación, ajusta esto
    # Si cambiaste a vale_salida_almacen_envasado_set:
    if hasattr(vale, 'vale_salida_almacen_envasado_set') and vale.vale_salida_almacen_envasado_set.exists():
        relacion_envasado = vale.vale_salida_almacen_envasado_set.first()
    
    # O si mantuviste el nombre original:
    # if vale.vale_salida_almacen_envasado_set.exists():  # Django crea este nombre por defecto
    
    # Calcular totales de valor si hay costos
    valor_total = 0
    for item in items_agrupados:
        if item['costo']:
            valor_total += float(item['cantidad']) * float(item['costo'])
    
    # Determinar estado para mostrar acciones disponibles
    puede_confirmar = vale.estado == 'borrador' and not vale.entrada  # Solo salidas en borrador
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
        'puede_confirmar': puede_confirmar,
        'puede_cancelar': puede_cancelar,
        'puede_despachar': puede_despachar,
        # 'form': form,  # Si mantienes el formulario
    }
    
    return render(request, 'movimientos/detalle_vale.html', context)


# Vista para confirmar una salida
def confirmar_salida(request, pk):
    vale = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('detalle_vale', pk=pk)
    
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
            
            # 2. Actualizar estado
            vale.estado = 'confirmado'
            vale.despachado_por = request.user
            vale.save()
            
            # 3. Aquí iría la lógica para actualizar inventarios
            # actualizar_inventarios(vale)
            
            messages.success(request, f'Vale {vale.consecutivo} confirmado exitosamente')
            
    except ValueError as e:
        messages.error(request, f'Error al confirmar: {str(e)}')
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
    
    return redirect('detalle_vale', pk=pk)


# Funciones auxiliares para validación
def validar_disponibilidad_mp(movimiento, almacen):
    """Validar disponibilidad de materia prima"""
    # Ajusta esto según tus modelos de inventario reales
    from inventario.models import Inv_Mat_Prima
    
    inventario = Inv_Mat_Prima.objects.filter(
        materia_prima=movimiento.materia_prima,
        almacen=almacen
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.materia_prima.nombre}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )

def validar_disponibilidad_producto(movimiento, almacen):
    """Validar disponibilidad de producto"""
    # Ajusta esto según tus modelos de inventario reales
    from inventario.models import Inv_Producto
    
    inventario = Inv_Producto.objects.filter(
        producto=movimiento.producto,
        almacen=almacen,
        lote=movimiento.lote
    ).first()
    
    if not inventario or inventario.cantidad < movimiento.cantidad:
        lote_info = f" (Lote: {movimiento.lote})" if movimiento.lote else ""
        raise ValueError(
            f'Cantidad insuficiente de {movimiento.producto.nombre_comercial}{lote_info}. '
            f'Disponible: {inventario.cantidad if inventario else 0}, '
            f'Solicitado: {movimiento.cantidad}'
        )

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