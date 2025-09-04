from django import forms
#from materia_prima.tipo_materia_prima.models import TipoMateriaPrima
from nomencladores.almacen.models import Almacen
from .models import MateriaPrima
from .choices import agregar_tipo_materia_prima, existe_tipo_materia_prima, obtener_tipos_materia_prima

class MateriaPrimaForm(forms.ModelForm):

    class Meta:
        model = MateriaPrima
        fields = ['tipo_materia_prima', 'nombre', 'unidad_medida', 'concentracion', 'conformacion',
                  'costo', 'ficha_tecnica', 'hoja_seguridad']
        widgets = {
            'tipo_materia_prima': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'concentracion': forms.NumberInput(attrs={'class': 'form-control'}),
            'conformacion': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ficha_tecnica': forms.FileInput(attrs={'class': 'form-control-file'}),
            'hoja_seguridad': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'tipo_materia_prima': 'Tipo de materia prima',
            'nombre': 'Nombre',
            'unidad_medida': 'Unidad de medida',
            'concentracion': 'Concentración',
            'conformacion': 'Conformación',
            'costo': 'Costo',
            'ficha_tecnica': 'Ficha técnica',
            'hoja_seguridad': 'Hoja de seguridad',
        }

class MateriaPrimaFormUpdate(forms.ModelForm):

    class Meta:
        model = MateriaPrima
        fields = [ 'nombre', 'unidad_medida', 'concentracion', 'conformacion',
                  'costo', 'ficha_tecnica', 'hoja_seguridad']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'concentracion': forms.NumberInput(attrs={'class': 'form-control'}),
            'conformacion': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ficha_tecnica': forms.FileInput(attrs={'class': 'form-control-file'}),
            'hoja_seguridad': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'nombre': 'Nombre',
            'unidad_medida': 'Unidad de medida',
            'concentracion': 'Concentración',
            'conformacion': 'Conformación',
            'costo': 'Costo',
        }

class AgregarTipoForm(forms.Form):
    valor = forms.CharField(
        max_length=50,
        label='Tipo de materia prima',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ej: aceites, esencias, etc.'
        }),
        help_text='Valor único en minúsculas, sin espacios (usar _ para separar)'
    )
    
    etiqueta = forms.CharField(
        max_length=100,
        label='Etiqueta visible',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ej: Aceites, Esencias, etc.'
        }),
        help_text='Nombre visible para los usuarios'
    )

    def clean_valor(self):
        valor = self.cleaned_data['valor'].lower().strip()
        
        # Validar formato
        if not valor.replace('_', '').isalnum():
            raise forms.ValidationError('Solo se permiten letras')
        
        # Validar que no exista
        if existe_tipo_materia_prima(valor):
            raise forms.ValidationError('Este tipo de materia prima ya existe')
        
        return valor

    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get('valor')
        etiqueta = cleaned_data.get('etiqueta')
        
        # Validar que no sea una combinación duplicada
        categorias = obtener_tipos_materia_prima()
        if valor and etiqueta and (valor, etiqueta) in categorias:
            raise forms.ValidationError('Esta combinación de valor y etiqueta ya existe')
        
        return cleaned_data