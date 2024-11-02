from django import forms
from envase_embalaje.formato.models import Formato

class FormatoForm(forms.ModelForm):
    class Meta:
        model = Formato
        fields = ['unidad_medida', 'capacidad']
        widgets = {
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'unidad_medida': 'Unidad de medida',
            'capacidad': 'Capacidad',
        }
