from django.shortcuts import render, get_object_or_404,redirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .models import Inv_Envase, Inv_Insumos, Inv_Mat_Prima, Inv_Producto
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import AjusteInvMPForm
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_MP
from nomencladores.models import Almacen
import decimal

# Create your views here.
def ajuste_inv_mp(request, inv_mp):
    inv_mat_prima = get_object_or_404(Inv_Mat_Prima, id=inv_mp)
    
    almacen = Almacen.objects.first()
    if request.user.groups.first().name == 'Almaceneros':
        almacen = Almacen.objects.filter(responsable=request.user).first()
        if not almacen or inv_mat_prima.almacen != almacen:
            messages.error(request,'No tienes permisos para ajustar este inventario')
            return redirect('materia_prima:materia_prima_list')

    if request.method == 'POST':
        print('En POST')
        nuevo_cant = decimal.Decimal(request.POST.get('cantidad'))
        viejo_cant = inv_mat_prima.cantidad
        print(nuevo_cant)
        print(viejo_cant)
        form = AjusteInvMPForm(request.POST, instance=inv_mat_prima, user=request.user)
        if form.is_valid():
            vale = Vale_Movimiento_Almacen(
                tipo = 'Ajuste de inventario',
                almacen = almacen
            )
            form.save()
            if nuevo_cant < viejo_cant:
                vale.entrada = False
            elif nuevo_cant > viejo_cant:
                vale.entrada = True
            else:
                messages.success(request, f'No se ha modificado la cantidad en inventario')   
                context = {
                    'form': form,
                    'inv': inv_mat_prima,
                }
                return render(request, 'inventario/actualizar_inv_mp.html', context) 
            print('A guardar la form')
            form.save()
            vale.save()
            messages.success(request, f'Inventario de {inv_mat_prima.materia_prima.nombre} actualizado correctamente')
            return redirect('materia_prima:materia_prima_list')
        else:
            print('La form no es valida')
            messages.success(request, f'Error en la form {form.errors}')
            return redirect('materia_prima:materia_prima_list')
    else:
        form = AjusteInvMPForm(instance=inv_mat_prima, user=request.user)

    context = {
        'form':form,
        'inv_mat_prima': inv_mat_prima,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'inventario/actualizar_inv_mp.html', context)