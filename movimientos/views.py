from django.forms import formset_factory
from .forms import RecepcionMateriaPrimaForm
from .models import Movimiento_MP, Vale_Movimiento_Almacen, Movimiento_EE, Movimiento_Ins
from adquisiciones.models import Adquisicion, DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo
from inventario.models import Inv_Mat_Prima, Inv_Insumos, Inv_Envase 
from django.shortcuts import render, redirect, get_object_or_404
import decimal


""" def recepcion_materia_prima(request, adq_id):
    CantidadFormSet = formset_factory(RecepcionMateriaPrimaForm, extra=1)
    adquisicion_O = get_object_or_404(Adquisicion, id=adq_id)
    almacen = adquisicion_O.detalles.first().almacen
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
            almacen = almacen
        )
        formset = CantidadFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    producto = form.cleaned_data['producto']
                    cantidad = form.cleaned_data['cantidad']                    
                    # Guardar en el modelo
                    Movimiento_MP.objects.create(
                        materia_prima=producto,
                        vale=vale,  # Ejemplo: atributo fijo
                        cantidad=cantidad,
                        entrada=True
                    )
            return redirect('login')
    else:
        formset = CantidadFormSet()

    return render(request, 'movimientos/recepcion_mp.html', {'formset': formset}) """

def recepcion_materia_prima(request, adq_id):
    print(adq_id)
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_mat = DetallesAdquisicion.objects.filter(adquisicion__id=adq_id)
    print(inv_mat)
    print(inv_mat.first())
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        print("Ya registrada en almacén")
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito        
    almacen = inv_mat.first().almacen
    if request.method == 'POST':
        print("En post")
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                entrada = True
            )
        print("Creado Vale")
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
                    adquisicion.registrada = True
                    adquisicion.save()
                except Exception as e: #(ValueError, TypeError):
                    print(f"Error...{e}")
                    pass
            else:
                print("No encontró cantidad")
        
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito
    
    # Si es GET, mostrar el formulario con los valores actuales
    return render(request, 'movimientos/recepcion_mp.html', {
        'productos': inv_mat
    })

def recepcion_envase(request, adq_id):
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_env = DetallesAdquisicionEnvase.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        print("Ya registrada en almacén")
        return redirect('envase_embalaje_lista')  # Redirigir a página de éxito        
    almacen = adquisicion.detalles_envases.first().almacen
    print(almacen)
    if request.method == 'POST':
        print("En post")
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                entrada=True
            )
        print("Creo vale")
        # Procesar cada producto
        for inv in inv_env:
            field_name = str(inv.envase_embalaje.codigo_envase)
            cantidad = decimal.Decimal('0.00')
            print(field_name)
            cantidad = decimal.Decimal(float(request.POST.get(field_name)))
            print(request.POST.get(field_name))
            print(cantidad)
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
        print("Ya registrada en almacén")
        return redirect('insumos_list')  # Redirigir a página de éxito        
    almacen = adquisicion.detalles_insumos.first().almacen
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen,
                entrada=True
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

def generar_vale(request, cons):
    pass

def movimiento_detalle(request, cons):
    pass