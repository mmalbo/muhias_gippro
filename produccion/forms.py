# forms.py
from django import forms

from materia_prima.models import MateriaPrima
from nomencladores.planta.models import Planta
# from producto_base.models import ProductoBase
from .models import Produccion
from envase_embalaje.models import EnvaseEmbalaje
class ProduccionForm(forms.ModelForm):
    """ envase_embalaje = forms.ModelChoiceField(
        queryset=EnvaseEmbalaje.objects.all(),
        label='Envase/Embalaje',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    materias_primas = forms.ModelMultipleChoiceField(
        queryset=MateriaPrima.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    materias_primas = forms.ModelMultipleChoiceField(
        queryset=MateriaPrima.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        required=False,
        label='Materias Primas:'
    )
    producto_base = forms.ModelMultipleChoiceField(
        queryset=ProductoBase.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        required=False,
        label='Productos bases:'
    ) """
    planta = forms.ModelChoiceField(queryset=Planta.objects.all(),
                                    label='Planta', widget=forms.Select(attrs={'class': 'form-control'})
                                    )

    class Meta:
        model = Produccion
        fields = [
            'lote',
            'nombre_producto',
            'prod_result',
            'cantidad_estimada',
            'pruebas_quimicas',
            'costo',
            'planta',
            # 'envase_embalaje',
            # 'materias_primas',
            # 'producto_base',
            'estado',
            # 'cantidad_materias_primas',

        ]
        widgets = {
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'prod_result': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:54%'}),
            'cantidad_estimada': forms.NumberInput(attrs={'class': 'form-control'}),
            'cantidad_materias_primas': forms.NumberInput(attrs={'class': 'form-control'}),
            'pruebas_quimicas': forms.FileInput(attrs={'class': 'form-control-file'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'lote': 'Lote',
            'nombre_producto': 'Nombre del Producto:',
            'prod_result': '¿Producto Terminado?:',
            'cantidad_estimada': 'Cantidad Estimada:',
            'pruebas_quimicas': 'Pruebas Químicas:',
            'costo': 'Costo:',
            'estado': 'Estado:',
        }
