from django import forms

from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen
from .models import Producto


class ProductoForm(forms.ModelForm):
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width:100%'}),
        required=False,
        label='Almacén:'
    )
    ficha_tecnica_folio = forms.ModelChoiceField(
        queryset=FichaTecnica.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width:100%'}),
        required=False,
        label='Ficha técnica:'
    )

    class Meta:
        model = Producto
        fields = ['codigo_producto', 'nombre_comercial', 'cantidad_alm', 'ficha_tecnica_folio', 'almacen',
                  'product_final', 'ficha_costo']
        labels = {
            'codigo_producto': 'Código del producto',
            'nombre_comercial': 'Nombre comercial',
            'cantidad_alm': 'Cantidad almacenada',
            'ficha_costo': 'Ficha costo',
            # 'ficha_tecnica_folio': 'Ficha técnica folio',
            'product_final': 'Producto final',
        }
        widgets = {
            'codigo_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_alm': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'ficha_tecnica_folio': forms.Select(attrs={'class': 'form-control'}),
            'ficha_costo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'product_final': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:70%'}),

            # 'almacen': forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        }
