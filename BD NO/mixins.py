from django.utils.timezone import now
from django.views.generic.edit import FormMixin

from bases.forms import (
    ModeloDenegacionModelForm,
    ModeloSuspensionModelForm,
    ModeloCancelacionModelForm,
)
from bases.models import ModeloTramitacionBase


class TramitacionFormMixin(FormMixin):
    def get_form_class(self):
        if self.object.estado == ModeloTramitacionBase.Estados.PENDIENTE:
            return ModeloDenegacionModelForm
        else:
            return ModeloSuspensionModelForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        causa = form.cleaned_data.get("causa")
        if isinstance(form, ModeloDenegacionModelForm):
            self.object.fecha_denegacion = now()
            self.object.causa_denegacion = causa
            self.object.estado = ModeloTramitacionBase.Estados.DENEGADO
        if isinstance(form, ModeloSuspensionModelForm):
            self.object.causa_suspension = now()
            self.object.causa_suspension = causa
            self.object.estado = ModeloTramitacionBase.Estados.SUPENDIDO
        if isinstance(form, ModeloCancelacionModelForm):
            self.object.causa_cancelacion = now()
            self.object.causa_cancelacion = causa
            self.object.estado = ModeloTramitacionBase.Estados.CANCELADO
        self.object.funcionario = self.request.user
        self.object.save()
        self.success_url = self.object.detalle_url()
        return super().form_valid(form)
