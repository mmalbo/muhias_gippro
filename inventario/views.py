from django.shortcuts import render, get_object_or_404,redirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from .models import Inv_Envase, Inv_Insumos, Inv_Mat_Prima, Inv_Producto
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import AjusteInvMPForm, AjusteInvEEForm, AjusteInvInsForm, AjusteInvProdForm
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_MP, Movimiento_EE, Movimiento_Ins, Movimiento_Prod
from nomencladores.models import Almacen
import decimal

# Create your views here.
def ajuste_inv_prod(request, inv_prod):
    inv_prod_o = get_object_or_404(Inv_Producto, id=inv_prod)
    print(inv_prod_o)
    
    almacen = Almacen.objects.first()
    if request.user.groups.first() and (request.user.groups.first().name == 'Almaceneros' or request.user.groups.first().name == 'Presidencia-Admin'):
        almacen = Almacen.objects.filter(responsable=request.user).first()
        if not almacen or inv_prod_o.almacen != almacen:
            messages.error(request,'No tienes permisos para ajustar este inventario')
            return redirect('producto_list')

    if request.method == 'POST':
        nuevo_cant = decimal.Decimal(request.POST.get('cantidad'))
        viejo_cant = inv_prod_o.cantidad
        print('Antes de form')
        form = AjusteInvProdForm(request.POST, instance=inv_prod_o, user=request.user)
        if form.is_valid():
            print(form.cleaned_data.get('causa'))
            causa = form.cleaned_data.get('causa')
            vale = Vale_Movimiento_Almacen.objects.create(
                tipo = 'Ajuste de inventario',
                descripcion=causa,
                origen=inv_prod_o.almacen,
                destino=inv_prod_o.almacen,
                almacen = inv_prod_o.almacen
            )
            print()
            form.save()
            print('Guardada la form')
            if nuevo_cant < viejo_cant:
                vale.entrada = False
            else:  
                """               nuevo_cant > viejo_cant: """
                vale.entrada = True
                """ else:
                messages.success(request, f'No se ha modificado la cantidad en inventario')   
                context = {
                    'form': form,
                    'inv': inv_prod_o,
                }
                return render(request, 'inventario/actualizar_inv_prod.html', context) """ 
            vale.save()
            ll = nuevo_cant - viejo_cant
            mov_prod = Movimiento_Prod.objects.create(
                producto = inv_prod_o.producto,
                vale = vale,
                cantidad = nuevo_cant - viejo_cant
            )
            try:
                mov_prod.save()
            except Exception as e:
                print(e)
            messages.success(request, f'Inventario de {inv_prod_o.producto} actualizado correctamente')
            return redirect('producto_list')
        else:
            print(f'La form no es valida {form.errors}')
            messages.success(request, f'Error en la form {form.errors}')
            return redirect('producto_list')
    else:
        form = AjusteInvProdForm(instance=inv_prod_o.producto, user=request.user)

    context = {
        'form':form,
        'inv_prod': inv_prod_o,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }
    print(context)

    return render(request, 'inventario/actualizar_inv_prod.html', context)

def ajuste_inv_mp(request, inv_mp):
    inv_mat_prima = get_object_or_404(Inv_Mat_Prima, id=inv_mp)
    
    almacen = Almacen.objects.first()
    if request.user.groups.first() and request.user.groups.first().name == 'Almaceneros':
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
            causa = form.cleaned_data.get('causa')
            vale = Vale_Movimiento_Almacen(
                tipo = 'Ajuste de inventario',
                descripcion=causa,
                origen=inv_mat_prima.almacen,
                destino=inv_mat_prima.almacen,
                almacen = inv_mat_prima.almacen
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
            vale.save()
            mov_mp = Movimiento_MP.objects.create(
                materia_prima = inv_mat_prima.materia_prima,
                vale = vale,
                cantidad = nuevo_cant - viejo_cant
            )
            mov_mp.save()
            print(mov_mp)
            print(mov_mp.vale)
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

def ajuste_inv_env(request, inv_ee):
    inv_env = get_object_or_404(Inv_Envase, id=inv_ee)
    
    almacen = Almacen.objects.first()
    if request.user.groups.first() and request.user.groups.first().name == 'Almaceneros':
        almacen = Almacen.objects.filter(responsable=request.user).first()
        if not almacen or inv_env.almacen != almacen:
            messages.error(request,'No tienes permisos para ajustar este inventario')
            return redirect('envase_embalaje:envase_embalaje_list')

    if request.method == 'POST':
        print('En POST')
        nuevo_cant = decimal.Decimal(request.POST.get('cantidad'))
        viejo_cant = inv_env.cantidad
        print(nuevo_cant)
        print(viejo_cant)
        form = AjusteInvEEForm(request.POST, instance=inv_env, user=request.user)
        if form.is_valid():
            causa = form.cleaned_data.get('causa')
            vale = Vale_Movimiento_Almacen.objects.create(
                tipo = 'Ajuste de inventario',
                descripcion=causa,
                origen=inv_env.almacen,
                destino=inv_env.almacen,
                almacen = inv_env.almacen
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
                    'inv': inv_env,
                }
                return render(request, 'inventario/actualizar_inv_env.html', context) 
            print('A guardar la form')
            vale.save()
            mov_ee = Movimiento_EE.objects.create(
                envase_embalaje = inv_env.envase,
                vale = vale,
                cantidad = nuevo_cant - viejo_cant
            )
            mov_ee.save()
            print(mov_ee)
            print(mov_ee.vale_e)
            messages.success(request, f'Inventario de {inv_env.envase.codigo_envase} actualizado correctamente')
            return redirect('materia_prima:materia_prima_list')
        else:
            print('La form no es valida')
            messages.success(request, f'Error en la form {form.errors}')
            return redirect('materia_prima:materia_prima_list')
    else:
        form = AjusteInvMPForm(instance=inv_env, user=request.user)

    context = {
        'form':form,
        'inv_env': inv_env,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'inventario/actualizar_inv_ee.html', context)

def ajuste_inv_ins(request, inv_ins):
    inv_insT = get_object_or_404(Inv_Insumos, id=inv_ins)
    
    almacen = Almacen.objects.first()
    if request.user.groups.first() and request.user.groups.first().name == 'Almaceneros':
        almacen = Almacen.objects.filter(responsable=request.user).first()
        if not almacen or inv_ins.almacen != almacen:
            messages.error(request,'No tienes permisos para ajustar este inventario')
            return redirect('InsumosOtros:insumos_list')

    if request.method == 'POST':
        print('En POST')
        nuevo_cant = decimal.Decimal(request.POST.get('cantidad'))
        viejo_cant = inv_insT.cantidad
        print(nuevo_cant)
        print(viejo_cant)
        form = AjusteInvInsForm(request.POST, instance=inv_insT, user=request.user)
        if form.is_valid():
            causa = form.cleaned_data.get('causa')
            vale = Vale_Movimiento_Almacen.objects.create(
                tipo = 'Ajuste de inventario',
                descripcion=causa,
                origen=inv_insT.almacen,
                destino=inv_insT.almacen,
                almacen = inv_insT.almacen
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
                    'inv': inv_insT,
                }
                return render(request, 'inventario/actualizar_inv_ins.html', context) 
            print('A guardar la form')
            vale.save()
            mov_ins = Movimiento_Ins.objects.create(
                insumo = inv_insT.insumos,
                vale = vale,
                cantidad = nuevo_cant - viejo_cant
            )
            mov_ins.save()
            messages.success(request, f'Inventario de {inv_insT.insumos} actualizado correctamente')
            return redirect('insumos_list')
        else:
            print('La form no es valida')
            messages.success(request, f'Error en la form {form.errors}')
            return redirect('insumos_list')
    else:
        form = AjusteInvMPForm(instance=inv_insT.insumos, user=request.user)

    context = {
        'form':form,
        'inv_ins': inv_insT,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'inventario/actualizar_inv_ins.html', context)