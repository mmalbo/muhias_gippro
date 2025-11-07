# forms.py
from django.utils import timezone
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
        fields = ['lote', 'nombre_producto', 'cantidad_estimada', 'costo', 'planta', 'prod_result']
        widgets = {
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_estimada': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prod_result': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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

class SubirPruebasQuimicasForm(forms.ModelForm):
    class Meta:
        model = Produccion
        fields = ['pruebas_quimicas', 'prod_conform']
        widgets = {
            'pruebas_quimicas': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            }),
            'prod_conform': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'pruebas_quimicas': 'Archivo de Pruebas (PDF, Excel, Imagen, etc.)',
            'prod_conform': 'Producto conforme'
        }
    
    def clean_archivo_pruebas(self):
        archivo = self.cleaned_data.get('pruebas_quimicas')
        if archivo:
            # Validar tamaño del archivo (5MB máximo)
            max_size = 5 * 1024 * 1024  # 5MB
            if archivo.size > max_size:
                raise forms.ValidationError("El archivo no puede ser mayor a 5MB")
            
            # Validar extensiones permitidas
            extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                                    '.jpg', '.jpeg', '.png']
            import os
            ext = os.path.splitext(archivo.name)[1].lower()
            if ext not in extensiones_permitidas:
                raise forms.ValidationError(
                    f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(extensiones_permitidas)}"
                )
        
        return archivo

class CancelarProduccionForm(forms.ModelForm):
    observaciones = forms.CharField(
        label="Observaciones de Cancelación",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa las razones por las cuales se cancela o detiene esta producción...',
            'required': True
        }),
        help_text="Este campo es obligatorio para cancelar una producción."
    )
    
    class Meta:
        model = Produccion
        fields = []  # No necesitamos campos del modelo directamente
    
    def __init__(self, *args, **kwargs):
        self.produccion = kwargs.pop('produccion', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        if self.produccion and self.produccion.puede_ser_cancelada():
            self.produccion.estado = 'Cancelada'
            self.produccion.observaciones_cancelacion = self.cleaned_data['observaciones']
            self.produccion.fecha_cancelacion = timezone.now()
            
            if commit:
                self.produccion.save()
        
        return self.produccion
            
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