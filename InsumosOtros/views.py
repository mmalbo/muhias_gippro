# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import InsumosOtros
from .forms import InsumosOtrosForm, InsumoUpdateForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from nomencladores.almacen.models import Almacen
from inventario.models import Inv_Insumos
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse, Http404

class ListInsumosView(ListView):
    model = InsumosOtros
    template_name = 'insumos/insumos_cat.html'
    context_object_name = 'insumos'
    #Hacer un query para mostrar solo los envases de un almacen si el usuario es almacenero, el almacen al que el pertenece

    def get_context_data(self, **kwargs):
        # Llama al método de la clase base
        context = super().get_context_data(**kwargs)

        # Agrega mensajes al contexto si existen
        if 'mensaje_error' in self.request.session:
            messages.error(self.request, self.request.session.pop('mensaje_error'))
        if 'mensaje_warning' in self.request.session:
            messages.warning(self.request, self.request.session.pop('mensaje_warning'))
        if 'mensaje_succes' in self.request.session:
            messages.success(self.request, self.request.session.pop('mensaje_succes'))
        return context

@login_required
def listInsumos(request):
    almacen_id = request.GET.get('almacen')
    producto_id = request.GET.get('producto')
    
    almacen = None
    if request.user.groups.filter(name='Almaceneros').exists():
        almacen = Almacen.objects.filter(responsable=request.user).first()

    insumo = Inv_Insumos.objects.select_related('insumos', 'almacen')
    
    if request.user.groups.filter(name='Presidencia-Admin').exists() or request.user.is_staff:
        if almacen_id and almacen_id != 'todos':
            insumo = insumo.filter(almacen=almacen_id)
    else:
        if almacen:
            insumo = insumo.filter(almacen=almacen)
        else:
            insumo = Inv_Insumos.objects.none()

    if producto_id:
        insumo = insumo.filter(insumos=producto_id)

    insumo = insumo.order_by('insumos__nombre', 'almacen__nombre')
    almacenes = Almacen.objects.all()
    productos = InsumosOtros.objects.all()
    total_productos = insumo.count()

    print(insumo)

    context = {
        'insumos':insumo,
        'almacenes':almacenes,
        'productos':productos,
        'almacen_id':almacen_id,
        'producto_id':producto_id,
        'almacen':almacen,
        'total_productos':total_productos,
        'es_admin': request.user.groups.filter(name='Presidencia-Admin').exists(),
        'es_almacenero': request.user.groups.filter(name='Almaceneros').exists(),
    }

    return render(request, 'insumos/insumos_list.html', context)

class UpdateInsumosView(UpdateView):
    model = InsumosOtros
    form_class = InsumoUpdateForm
    template_name = 'insumos/insumos_form.html'
    success_url = reverse_lazy('insumo_lista')  # Cambia esto al nombre de tu URL

    def form_valid(self, form):
        messages.success(self.request, "Se ha actualizado correctamente el insumo.")
        return super().form_valid(form)


class DeleteInsumoView(DeleteView):
    model = InsumosOtros
    template_name = 'insumos/insumos_confirm_delete.html'
    success_url = reverse_lazy('insumo_list')  # Cambia esto al nombre de tu URL

def get_insumo(request, pk):
    try:
        almacen = Almacen.objects.get(pk=pk)
        insumos = almacen.insumos.all()
        insumo_data = [{'nombre': insumo.nombre, 'nombre_almacen': almacen.nombre} for insumo in
                                insumos]

        return JsonResponse(insumo_data, safe=False)
    except Almacen.DoesNotExist:
        raise Http404("Insumo no encontrado")

class CreateImportView(CreateView):
    model = InsumosOtros
    form_class = InsumosOtrosForm
    template_name = 'insumos/import_form.html'
    success_url = '/insumo/'
    success_message = "Se ha importado correctamente el insumo."



class InsumoCreateView(CreateView):
    model = InsumosOtros
    form_class = InsumosOtrosForm
    template_name = 'insumos/insumos_form.html'
    success_url = reverse_lazy('insumo_lista')
    success_message = "Se ha creado correctamente el insumo."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['almacenes'] = InsumosOtros.objects.all()
        return context
    
""" def insumos_list(request):
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
    return render(request, 'insumos/insumos_detail.html', {'insumo': insumo}) """
