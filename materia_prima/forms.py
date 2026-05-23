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

        def __init__(self, *args, **kwargs):
            super(MateriaPrimaForm, self).__init__(*args, **kwargs)
            self.fields['hoja_seguridad'].widget.attrs = {
            'required': False}
            self.fields['ficha_tecnica'].widget.attrs = {
            'required': False}
            
            
class MateriaPrimaCostoForm(forms.ModelForm):

    class Meta:
        model = MateriaPrima
        fields = ['nombre', 'costo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre',
            'costo': 'Costo',
        }
        
class MateriaPrimaFormUpdate(forms.ModelForm):
    # Campos que no deben editarse en update (solo lectura)
    codigo = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = MateriaPrima
        fields = [
            'codigo',  # Solo lectura en update
            'nombre',
            'tipo_materia_prima',  # Añadido
            'unidad_medida',
            'concentracion',
            'conformacion',
            'costo',
            'ficha_tecnica',
            'hoja_seguridad'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_materia_prima': forms.Select(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'concentracion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'conformacion': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ficha_tecnica': forms.FileInput(attrs={'class': 'form-control-file'}),
            'hoja_seguridad': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'tipo_materia_prima': 'Tipo de materia prima',
            'unidad_medida': 'Unidad de medida',
            'concentracion': 'Concentración (%)',
            'conformacion': 'Conformación',
            'costo': 'Costo ($)',
            'ficha_tecnica': 'Ficha técnica',
            'hoja_seguridad': 'Hoja de seguridad',
        }
        help_texts = {
            'concentracion': 'Ingrese la concentración en porcentaje (ej: 99.5)',
            'costo': 'Costo por unidad de medida',
        }

    def __init__(self, *args, **kwargs):
        super(MateriaPrimaFormUpdate, self).__init__(*args, **kwargs)
        
        # Hacer campos opcionales
        self.fields['concentracion'].required = False
        self.fields['conformacion'].required = False
        self.fields['tipo_materia_prima'].required = True

        # Lógica para el campo código
        if self.instance and self.instance.pk and self.instance.codigo:
            # Si ya tiene un código válido, hacerlo readonly
            self.fields['codigo'].widget.attrs['readonly'] = 'readonly'
            self.fields['codigo'].help_text = "El código no puede modificarse porque ya tiene un valor asignado"
        else:
            # Si es nuevo o el código está vacío, permitir edición
            self.fields['codigo'].required = True
            self.fields['codigo'].help_text = "Ingrese un código único para esta materia prima"
            
        # Si es una actualización (tiene instance), mostrar nombres de archivos actuales
        if self.instance and self.instance.pk:
            if self.instance.ficha_tecnica:
                self.fields['ficha_tecnica'].help_text = f'Actual: {self.instance.get_ficha_tecnica_name()}'
            if self.instance.hoja_seguridad:
                self.fields['hoja_seguridad'].help_text = f'Actual: {self.instance.get_hoja_seguridad_name()}'

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        instance = self.instance
        
        # Si es una actualización y ya tenía código, no permitir cambios
        if instance and instance.pk and instance.codigo:
            if codigo != instance.codigo:
                raise forms.ValidationError("No se puede modificar el código porque ya tiene un valor asignado.")
            return codigo

        # Si es nuevo o no tenía código, validar que no esté vacío
        if not codigo:
            raise forms.ValidationError("El código es obligatorio.")
        
        # Validar unicidad
        if MateriaPrima.objects.exclude(pk=instance.pk if instance else None).filter(codigo=codigo).exists():
            raise forms.ValidationError("Ya existe una materia prima con este código.")
        
        return codigo
            
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