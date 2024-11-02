# forms.py
from django import forms
from .models import TipoMateriaPrima

class TipoMateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = TipoMateriaPrima
        # fields = '__all__'
        fields = [
            'nombre',
            'tipo',
            'ingrediente_activo',
            'tipo_fragancia',
            'tipo_sustancia',
            'tipo_color',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleFields()'}),
            'tipo_fragancia': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'id_tipo_fragancia'}),
            'tipo_sustancia': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_color': forms.TextInput(attrs={'class': 'form-control'}),
            'ingrediente_activo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre',
            'tipo': 'Tipo',
            'ingrediente_activo': 'Ingrediente activo',
            'tipo_fragancia': 'Tipo fragancia',
            'tipo_sustancia': 'Tipo sustancia',
            'tipo_color': 'Tipo color',
        }
