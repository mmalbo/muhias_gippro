# forms.py
from django import forms

from materia_prima.models import MateriaPrima
from nomencladores.planta.models import Planta
from nomencladores.almacen.models import Almacen
from .models import Produccion, Prod_Inv_MP


class ProduccionForm(forms.ModelForm):
    planta = forms.ModelChoiceField( queryset=Planta.objects.all(), 
                                    widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    
    class Meta:
        model = Produccion
        fields = ['lote', 'nombre_producto', 'cantidad_estimada', 'costo', 'pruebas_quimicas', 'planta']
        widgets = {
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_estimada': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pruebas_quimicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            #'planta': forms.Select(attrs={'class': 'form-control'}),
        }

class MateriaPrimaForm(forms.Form):
    materia_prima = forms.ModelChoiceField(
        queryset=MateriaPrima.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    cantidad = forms.DecimalField(
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        required=True
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar la representación de las materias primas
        self.fields['materia_prima'].label_from_instance = lambda obj: f"{obj.nombre} ({obj.conformacion} - {obj.unidad_medida})"

        
""" class ProduccionForm(forms.ModelForm):    
    planta = forms.ModelChoiceField(queryset=Planta.objects.all(),
                                    label='Planta', 
                                    widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = Produccion
        fields = ['lote','nombre_producto','cantidad_estimada',
            'costo','planta',]
        widgets = {
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_estimada': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'lote': 'Lote',
            'nombre_producto': 'Nombre del Producto:',
            'cantidad_estimada': 'Cantidad Estimada:',
            'costo': 'Costo:',
        }

class Inv_MP_Form(forms.ModelForm):    
    class Meta:
        model = Prod_Inv_MP
        fields = ['inv_materia_prima', 'cantidad_materia_prima']
        widgets = {
            'inv_materia_prima': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_materia_prima': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inv_materia_prima'].queryset = Inv_MP_Form.objects.all().order_by('materia_prima')
        self.fields['inv_materia_prima'].label_from_instance = lambda obj: f"{obj.materia_prima.nombre} ({obj.materia_prima.unidad_medida})"

class PruebasQuimicasForm(forms.ModelForm):
    class Meta:
        model = Produccion
        fields = ['pruebas_quimicas']
        widgets = {
            'pruebas_quimicas': forms.FileInput(attrs={'class': 'form-control'}),
        }    """     