from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import FichaCosto
from .forms import FichaCostoForm, FichaCostoFilterForm

# Vista basada en funciones para listar
def lista_fichas_costo(request):
    """
    Vista para listar todas las fichas de costo con opción de búsqueda y filtrado
    """
    fichas = FichaCosto.objects.all().order_by('-id')
    
    # Aplicar filtros si existen
    activo = request.GET.get('activo')
    if activo is not None and activo != '':
        fichas = fichas.filter(activo=activo == 'True')
    
    # Búsqueda por texto
    search_query = request.GET.get('search', '')
    if search_query:
        fichas = fichas.filter(
            Q(id__icontains=search_query) |
            Q(costo_x_itro__icontains=search_query) |
            Q(utilidad__icontains=search_query)
        )
    
    form_filtro = FichaCostoFilterForm(request.GET or None)
    
    context = {
        'fichas': fichas,
        'form_filtro': form_filtro,
        'search_query': search_query,
        'total_fichas': fichas.count(),
    }
    
    return render(request, 'FichaCosto/lista.html', context)

# Vista basada en clases para listar (alternativa)
class FichaCostoListView(LoginRequiredMixin, ListView):
    model = FichaCosto
    template_name = 'FichaCosto/lista.html'
    context_object_name = 'fichas'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-id')
        
        # Filtros
        activo = self.request.GET.get('activo')
        if activo is not None and activo != '':
            queryset = queryset.filter(activo=activo == 'True')
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(costo_x_itro__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_filtro'] = FichaCostoFilterForm(self.request.GET or None)
        context['search_query'] = self.request.GET.get('search', '')
        return context

# Vista para crear
def crear_ficha_costo(request):
    """
    Vista para crear una nueva ficha de costo
    """
    if request.method == 'POST':
        form = FichaCostoForm(request.POST)
        if form.is_valid():
            ficha = form.save()
            messages.success(request, f'Ficha de costo #{ficha.id} creada exitosamente.')
            return redirect('fichas_costo:lista')
    else:
        form = FichaCostoForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Ficha de Costo',
        'accion': 'Crear',
    }
    
    return render(request, 'FichaCosto/formulario.html', context)

# Vista basada en clases para crear (alternativa)
class FichaCostoCreateView(LoginRequiredMixin, CreateView):
    model = FichaCosto
    form_class = FichaCostoForm
    template_name = 'FichaCosto/formulario.html'
    success_url = reverse_lazy('fichas_costo:lista')
    
    def form_valid(self, form):
        messages.success(self.request, 'Ficha de costo creada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Ficha de Costo'
        context['accion'] = 'Crear'
        return context

# Vista para editar
def editar_ficha_costo(request, pk):
    """
    Vista para editar una ficha de costo existente
    """
    ficha = get_object_or_404(FichaCosto, pk=pk)
    
    if request.method == 'POST':
        form = FichaCostoForm(request.POST, instance=ficha)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ficha de costo #{ficha.id} actualizada exitosamente.')
            return redirect('fichas_costo:lista')
    else:
        form = FichaCostoForm(instance=ficha)
    
    context = {
        'form': form,
        'ficha': ficha,
        'titulo': f'Editar Ficha de Costo #{ficha.id}',
        'accion': 'Actualizar',
    }
    
    return render(request, 'FichaCosto/formulario.html', context)

# Vista basada en clases para editar (alternativa)
class FichaCostoUpdateView(LoginRequiredMixin, UpdateView):
    model = FichaCosto
    form_class = FichaCostoForm
    template_name = 'FichaCosto/formulario.html'
    success_url = reverse_lazy('fichas_costo:lista')
    
    def form_valid(self, form):
        messages.success(self.request, 'Ficha de costo actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Ficha de Costo #{self.object.id}'
        context['accion'] = 'Actualizar'
        return context

# Vista para eliminar
def eliminar_ficha_costo(request, pk):
    """
    Vista para eliminar una ficha de costo (con confirmación)
    """
    ficha = get_object_or_404(FichaCosto, pk=pk)
    
    if request.method == 'POST':
        ficha_id = ficha.id
        ficha.delete()
        messages.success(request, f'Ficha de costo #{ficha_id} eliminada exitosamente.')
        return redirect('fichas_costo:lista')
    
    context = {
        'ficha': ficha,
    }
    
    return render(request, 'FichaCosto/eliminar.html', context)

# Vista basada en clases para eliminar (alternativa)
class FichaCostoDeleteView(LoginRequiredMixin, DeleteView):
    model = FichaCosto
    template_name = 'FichaCosto/eliminar.html'
    success_url = reverse_lazy('fichas_costo:lista')
    
    def delete(self, request, *args, **kwargs):
        ficha = self.get_object()
        ficha_id = ficha.id
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Ficha de costo #{ficha_id} eliminada exitosamente.')
        return response

# Vista para detalle
def detalle_ficha_costo(request, pk):
    """
    Vista para ver el detalle de una ficha de costo
    """
    ficha = get_object_or_404(FichaCosto, pk=pk)
    
    context = {
        'ficha': ficha,
    }
    
    return render(request, 'FichaCosto/detalle.html', context)

# Vista basada en clases para detalle (alternativa)
class FichaCostoDetailView(LoginRequiredMixin, DetailView):
    model = FichaCosto
    template_name = 'FichaCosto/detalle.html'
    context_object_name = 'ficha'