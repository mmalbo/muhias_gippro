# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import InsumosOtros
from .forms import InsumosOtrosForm


def insumos_list(request):
    insumos = InsumosOtros.objects.all()
    return render(request, 'insumos/insumos_list.html', {'insumos': insumos})


def insumos_create(request):
    if request.method == 'POST':
        form = InsumosOtrosForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('insumos_list')
    else:
        form = InsumosOtrosForm()
    return render(request, 'insumos/insumos_form.html', {'form': form})


def insumos_update(request, pk):
    insumo = get_object_or_404(InsumosOtros, pk=pk)
    if request.method == 'POST':
        form = InsumosOtrosForm(request.POST, instance=insumo)
        if form.is_valid():
            form.save()
            return redirect('insumos_list')
    else:
        form = InsumosOtrosForm(instance=insumo)
    return render(request, 'insumos/insumos_form.html', {'form': form})


def insumos_delete(request, pk):
    insumo = get_object_or_404(InsumosOtros, pk=pk)
    if request.method == 'POST':
        insumo.delete()
        return redirect('insumos_list')
    return render(request, 'insumos/insumos_confirm_delete.html', {'insumo': insumo})


# Nueva vista para ver detalles
def insumos_detail(request, pk):
    insumo = get_object_or_404(InsumosOtros, pk=pk)
    return render(request, 'insumos/insumos_detail.html', {'insumo': insumo})
