from django import forms
from materia_prima.models import MateriaPrima
from adquisiciones.models import Adquisicion

class RecepcionMateriaPrimaForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=MateriaPrima.objects.all(),
        label="Seleccionar materia prima"
    )
    cantidad = forms.FloatField(
        label="Cantidad recibida",
        widget=forms.NumberInput(attrs={'step': '0.10'})
    )