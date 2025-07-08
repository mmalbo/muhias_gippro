from django import forms
from materia_prima.tipo_materia_prima.models import TipoMateriaPrima
from nomencladores.almacen.models import Almacen
from .models import MateriaPrima


class MateriaPrimaForm(forms.ModelForm):
    tipo_materia_prima = forms.ModelChoiceField(
        queryset=TipoMateriaPrima.objects.all(),
        label='Tipo de materia prima',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        label='Almacén',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = MateriaPrima
        fields = ['codigo', 'nombre', 'unidad_medida', 'concentracion', 'conformacion',
                  'costo', 'ficha_tecnica', 'hoja_seguridad', 'tipo_materia_prima',
                  'almacen', 'cantidad_almacen']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'concentracion': forms.NumberInput(attrs={'class': 'form-control'}),
            'conformacion': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_almacen': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ficha_tecnica': forms.FileInput(attrs={'class': 'form-control-file'}),
            'hoja_seguridad': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'tipo_materia_prima': 'Tipo de materia prima',
            'cantidad_almacen': 'Cantidad',
            'codigo': 'Código',
            'nombre': 'Nombre',
            'unidad_medida': 'Unidad de medida',
            'concentracion': 'Concentración',
            'conformacion': 'Conformación',
            'costo': 'Costo',
            'almacen': 'Almacen',
        }


class MateriaPrimaFormUpdate(forms.ModelForm):
    tipo_materia_prima = forms.ModelChoiceField(
        queryset=TipoMateriaPrima.objects.all(),
        label='Tipo de materia prima',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    almacen = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                     label='Almacen',
                                     widget=forms.Select(attrs={'class': 'form-control'})
                                     )

    class Meta:
        model = MateriaPrima
        fields = ['codigo', 'nombre', 'unidad_medida', 'concentracion', 'conformacion',
                  'costo', 'ficha_tecnica', 'hoja_seguridad', 'tipo_materia_prima',
                  'almacen', 'cantidad_almacen']
        widgets = {
            'codigo': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'concentracion': forms.NumberInput(attrs={'class': 'form-control'}),
            'conformacion': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_almacen': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ficha_tecnica': forms.FileInput(attrs={'class': 'form-control-file'}),
            'hoja_seguridad': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'tipo_materia_prima': 'Tipo de materia prima',
            'cantidad_almacen': 'Cantidad',
            'codigo': 'Código',
            'nombre': 'Nombre',
            'unidad_medida': 'Unidad de medida',
            'concentracion': 'Concentración',
            'conformacion': 'Conformación',
            'costo': 'Costo',
            'almacen': 'Almacen',
        }
