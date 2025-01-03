# forms.py
from django import forms
from nomencladores.almacen.models import Almacen
from .models import InsumosOtros


class InsumosOtrosForm(forms.ModelForm):
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        label='Almacén',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    costo = forms.FloatField(
        required=True,
        min_value=0,  # Asegura que el costo mínimo sea 0
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    cantidad_almacen = forms.IntegerField(
        required=True,
        min_value=0,  # Asegura que la cantidad mínima sea 0
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = InsumosOtros
        fields = ['codigo', 'estado', 'nombre', 'descripcion', 'cantidad_almacen', 'costo', 'almacen']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }