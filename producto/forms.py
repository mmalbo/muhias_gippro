from django import forms

from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen
from .models import Producto


class ProductoForm(forms.ModelForm):
    """ almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width:100%'}),
        required=False,
        label='Almacén:'
    ) """
    """ ficha_tecnica_folio = forms.ModelChoiceField(
        queryset=FichaTecnica.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width:100%'}),
        required=False,
        label='Ficha técnica:'
    ) """

    class Meta:
        model = Producto
        fields = ['codigo_producto', 'codigo_3l', 'nombre_comercial', 'ficha_tecnica_folio', 'formato',
                  'ficha_costo']
        labels = {
            'codigo_producto': 'Código del producto',
            'codigo_3l': 'Código de 3 dígitos',
            'nombre_comercial': 'Nombre comercial',
            'ficha_costo': 'Ficha costo',
            'ficha_tecnica_folio': 'Ficha técnica folio',
            'formato': 'Formato',
        }
        widgets = {
            'codigo_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'ficha_tecnica_folio': forms.FileInput(attrs={'class': 'form-control-file'}),
            'ficha_costo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'formato': forms.Select(attrs={'class': 'form-select'}),            
            # 'almacen': forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        }
