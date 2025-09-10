from django.forms import formset_factory
from .forms import RecepcionMateriaPrimaForm
from .models import Movimiento_MP, Vale_Movimiento_Almacen
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
    # Obtener los productos que quieres mostrar (ejemplo: todos)
    inv_mat = DetallesAdquisicion.objects.filter(adquisicion__id=adq_id)
    adquisicion = get_object_or_404(Adquisicion, id=adq_id)
    if adquisicion.registrada:
        print("Ya registrada en almacén")
        return redirect('materia_prima:materia_prima_list')  # Redirigir a página de éxito        
    almacen = adquisicion.detalles.first().almacen
    if request.method == 'POST':
        vale = Vale_Movimiento_Almacen.objects.create(
                almacen = almacen
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
                        cantidad=cantidad,
                        entrada=True
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