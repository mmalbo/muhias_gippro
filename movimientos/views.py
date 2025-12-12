from django.forms import formset_factory
from .forms import RecepcionMateriaPrimaForm, MovimientoFormUpdate
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .models import Movimiento_MP, Vale_Movimiento_Almacen, Movimiento_EE, Movimiento_Ins
from adquisiciones.models import Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo
from inventario.models import Inv_Mat_Prima, Inv_Insumos, Inv_Envase 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .movimientos import export_vale
import decimal
from django.contrib.auth.models import Group
from utils.models import Notification
from adquisiciones.models import Adquisicion
from produccion.models import Prod_Inv_MP, Produccion

def solicitud_salida(request):
    pass

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
    print(adquisicion)
    if adquisicion.registrada:
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    print(almacen)
    print(almacen.id)
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = 'Adquisición',
                destino = almacen.nombre,
                entrada = True,
                tipo = 'Recepción'
            )
        # Procesar cada producto
        for inv in inv_mat:
            field_name = str(inv.materia_prima.id)
            cantidad = decimal.Decimal('0.00')
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            if cantidad:
                try:
                    Movimiento_MP.objects.create(
                        materia_prima=inv.materia_prima,
                        vale=vale,  # Ejemplo: atributo fijo
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
                    adquisicion.registrada = True
                    adquisicion.save()
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass
            else:
                print("No encontro cantidad")
        
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
        print("Ya registrada en almacén")
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito        
    almacen = adquisicion.almacen
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                origen = 'Adquisición',
                destino = almacen.nombre,
                entrada=True,
                tipo = 'Recepción'
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
                        vale_e=vale,  # Ejemplo: atributo fijo
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
                    adquisicion.registrada = True
                    adquisicion.save()
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No se encontro cantidad")
        
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
                origen = 'Adquisición',
                destino = almacen.nombre,
                entrada=True,
                tipo = 'Recepción'
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
                        vale_e=vale,  # Ejemplo: atributo fijo
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
                    adquisicion.registrada = True
                    adquisicion.save()
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}") 
                    pass
            else:
                print("No encontró cantidad")
        
        return redirect('insumos_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_ins.html', {
        'productos': inv_ins
    })

def movimiento_list(request):
    movimientos = Vale_Movimiento_Almacen.objects.all()
    return render(request, 'movimientos/movimientos_list.html', {
        'movimientos': movimientos
    })

def recepciones_pendientes_list(request):
    rec_pendientes = Adquisicion.objects.filter(registrada=False).all()
    almacen = request.user
    print(rec_pendientes)
    print(f'almacen{almacen}')
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

def vale_detalle(request, pk):
    print(pk)
    vale = get_object_or_404(Vale_Movimiento_Almacen, id=pk)
    tipo = vale.tipo
    print(f'tipo: {tipo}')
    if request.method == 'POST':
        form = MovimientoFormUpdate(request.POST, instance=vale) 
        if form.is_valid():
            form.save()
            print('Actualizado correctamente')
            messages.success(request, 'Actualizado correctamente')
            return redirect('materia_prima:materia_prima_list') 
        else:
            print(f'Error en la form: {form.errors}')
            messages.error(request, f'Error en la form: {form.errors}')
            return redirect('materia_prima:materia_prima_list')
    form = MovimientoFormUpdate(instance=vale)
    if vale.tipo == 'Solicitud':
        activos = vale.mp_produccion.all()
        if activos:
            tipo = 'Solicitud'
        else:
            print('No se encontró solicitudes de este vale')
    elif vale.tipo == 'Recepción':
        print('En recepcion')
        activos = vale.movimientos.all()
        print(activos)
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
    elif vale.tipo == 'Entrega' or vale.tipo == 'Conduce':
        activos = vale.movimientos.all()
        if activos:
            tipo = 'materias primas'
        else:
            activos = vale.movimientos_e.all()
            if activos:
                tipo = 'envases y embalajes'
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
                tipo = 'envase y embalajes'
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

    print(f'context:{context}')

    return render(request, 'movimientos/movimiento_update.html', context)

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