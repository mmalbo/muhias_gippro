from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import (
    FormView,
    CreateView,
    UpdateView,
    DetailView,
)
from django.views.generic.base import ContextMixin, View, TemplateView
# from django_filters.views import FilterView
# from django_tables2 import SingleTableMixin
# from django_tables2.export import ExportMixin


class BaseView(ContextMixin, View):
    model = None
    form_class = None
    table_class = None
    serializer_class = None
    filterset_class = None

    def filter_url(self):
        return reverse_lazy(
            f"{self.model._meta.verbose_name_plural.replace(' de ', '_').replace(' ', '_')}:filtro"
        )

    def get_queryset(self):
        return self.model.objects.all()


class ModeloBaseTemplateView(TemplateView):
    pass


class ModeloBaseFormView(FormView):
    pass


# class ModeloBaseFilterView(ExportMixin, SingleTableMixin, FilterView):
#     template_name = "bases/paginas/filter.html"
#     paginate_by = 6
#
#     def get_export_filename(self, export_format):
#         return f"{self.generar_nombre()}.{export_format}"
#
#     def generar_nombre(self):
#         fecha_actual = now().strftime("%Y%m%d")
#         app_label = self.model._meta.app_label
#         nombre_aplicacion = self.model._meta.verbose_name_plural.replace(
#             " de ", "_"
#         ).replace(" ", "_")
#         if app_label == nombre_aplicacion:
#             return "_".join(["lot", fecha_actual, app_label])
#         return "_".join(["lot", fecha_actual, app_label, nombre_aplicacion])


class ModeloBaseCreateView(CreateView):
    template_name = "bases/paginas/form.html"

    def form_valid(self, form):
        messages.success(
            self.request, f"{self.model._meta.verbose_name.capitalize()} creado"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "")
        return super().form_invalid(form)


class ModeloBaseUpdateView(UpdateView):
    def form_valid(self, form):
        messages.success(
            self.request, f"{self.object.verbose_name().capitalize()} actualizado"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "")
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Exception as e:
            messages.error(self.request, e)
            return redirect(self.filter_url())
        return super().get(request, *args, **kwargs)


class ModeloBaseDetailView(DetailView):
    template_name = "bases/paginas/detail.html"
