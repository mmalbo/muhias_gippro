from django import forms
from .models import Caja


class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['codigo','nombre', 'tamanno', 'material' ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tamanno': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),

        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'tamanno': 'Tamaño',
            'material': 'Material',
        }
