from django import forms
from .models import Planta


class PlantaForm(forms.ModelForm):
    class Meta:
        model = Planta
        fields = [
            'nombre',
            'propio',
            'almacen',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'propio': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:90%'}),
            'almacen': forms.Select(attrs={'class': 'form-control', 'style': 'right:90%'}),
        }
        labels = {
            'nombre': 'Nombre:',
            'propio': 'Propia:',
            'almacen': 'Almacén asociado',
        }
