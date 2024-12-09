from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import MateriaPrimaAdquisicion, EnvaseAdquisicion, InsumosAdquisicion
from .forms import MateriaPrimaAdquisicionForm, EnvaseAdquisicionForm, InsumosAdquisicionForm


# Vistas para MateriaPrimaAdquisicion
class MateriaPrimaAdquisicionListView(ListView):
    model = MateriaPrimaAdquisicion
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_list.html'
    context_object_name = 'adquisiciones'


class MateriaPrimaAdquisicionDetailView(DetailView):
    model = MateriaPrimaAdquisicion
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_detail.html'
    context_object_name = 'adquisicion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context


class MateriaPrimaAdquisicionCreateView(CreateView):
    model = MateriaPrimaAdquisicion
    form_class = MateriaPrimaAdquisicionForm
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_form.html'
    success_url = reverse_lazy('materia_prima_adquisicion_list')

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de materia prima creada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


class MateriaPrimaAdquisicionUpdateView(UpdateView):
    model = MateriaPrimaAdquisicion
    form_class = MateriaPrimaAdquisicionForm
    template_name = 'adquisicion/materia_prima/materia_prima_adquisicion_form.html'
    success_url = reverse_lazy('materia_prima_adquisicion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de materia prima actualizada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


# Vistas para EnvaseAdquisicion
class EnvaseAdquisicionListView(ListView):
    model = EnvaseAdquisicion
    template_name = 'adquisicion/envase/envase_adquisicion_list.html'
    context_object_name = 'adquisiciones'


class EnvaseAdquisicionDetailView(DetailView):
    model = EnvaseAdquisicion
    template_name = 'adquisicion/envase/envase_adquisicion_detail.html'
    context_object_name = 'adquisicion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context


class EnvaseAdquisicionCreateView(CreateView):
    model = EnvaseAdquisicion
    form_class = EnvaseAdquisicionForm
    template_name = 'adquisicion/envase/envase_adquisicion_form.html'
    success_url = reverse_lazy('envase_adquisicion_list')

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de envase creada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


class EnvaseAdquisicionUpdateView(UpdateView):
    model = EnvaseAdquisicion
    form_class = EnvaseAdquisicionForm
    template_name = 'adquisicion/envase/envase_adquisicion_form.html'
    success_url = reverse_lazy('envase_adquisicion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de envase actualizada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


# Vistas para InsumosAdquisicion
class InsumosAdquisicionListView(ListView):
    model = InsumosAdquisicion
    template_name = 'adquisicion/insumos/insumos_adquisicion_list.html'
    context_object_name = 'adquisiciones'


class InsumosAdquisicionDetailView(DetailView):
    model = InsumosAdquisicion
    template_name = 'adquisicion/insumos/insumos_adquisicion_detail.html'
    context_object_name = 'adquisicion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context


class InsumosAdquisicionCreateView(CreateView):
    model = InsumosAdquisicion
    form_class = InsumosAdquisicionForm
    template_name = 'adquisicion/insumos/insumos_adquisicion_form.html'
    success_url = reverse_lazy('insumos_adquisicion_list')

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de insumos creada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


class InsumosAdquisicionUpdateView(UpdateView):
    model = InsumosAdquisicion
    form_class = InsumosAdquisicionForm
    template_name = 'adquisicion/insumos/insumos_adquisicion_form.html'
    success_url = reverse_lazy('insumos_adquisicion_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.factura:
            context['nombre_factura'] = self.object.factura.name.split('/')[-1]
        else:
            context['nombre_factura'] = None
        return context

    def form_valid(self, form):
        messages.success(self.request, "Adquisición de insumos actualizada con éxito.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)