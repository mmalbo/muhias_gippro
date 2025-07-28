from django.forms import formset_factory
from .forms import RecepcionMateriaPrimaForm
from .models import Movimiento_MP, Vale_Movimiento_Almacen
from adquisiciones.models import Adquisicion
from django.shortcuts import render, redirect, get_object_or_404

def recepcion_materia_prima(request, adq_id):
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

    return render(request, 'movimientos/recepcion_mp.html', {'formset': formset})