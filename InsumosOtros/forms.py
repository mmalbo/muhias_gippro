# forms.py
from django import forms
from nomencladores.almacen.models import Almacen
from .models import InsumosOtros
from django.apps import apps

class InsumosOtrosForm(forms.ModelForm):
    almacen = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Almacenes'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Almacen = apps.get_model('almacen', 'Almacen')
        self.fields['almacen'].queryset = Almacen.objects.all()

    class Meta:
        model = InsumosOtros
        fields = [
            'nombre',
            'descripcion',
            'almacen',
        ]
        widgets = {
            # 'codigo_envase': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            # 'codigo_envase': 'Código de envace:',
            'cantidad': 'Cantidad:',
        }

class InsumoUpdateForm(forms.ModelForm):
    
    class Meta:
        model = InsumosOtros
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'costo',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'costo': 'Costo ($)',
        }
        help_texts = {
            'codigo': 'Código único del insumo',
            'costo': 'Costo unitario del insumo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos opcionales
        self.fields['descripcion'].required = True
        self.fields['costo'].required = False
        self.fields['costo'].initial = 0
        
        # Lógica para el campo código
        instance = self.instance
        if instance and instance.pk and instance.codigo and instance.codigo.strip():
            # Si ya tiene un código válido (no vacío), hacerlo readonly
            self.fields['codigo'].widget.attrs['readonly'] = 'readonly'
            self.fields['codigo'].widget.attrs['class'] = 'form-control bg-light'
            self.fields['codigo'].help_text = "El código no puede modificarse porque ya tiene un valor asignado"
            self.fields['codigo'].required = False
        else:
            # Si es nuevo o el código está vacío, permitir edición
            self.fields['codigo'].required = True
            self.fields['codigo'].widget.attrs['readonly'] = False
            self.fields['codigo'].help_text = "Ingrese un código único para este insumo"
            # Eliminar disabled si existe
            if 'disabled' in self.fields['codigo'].widget.attrs:
                del self.fields['codigo'].widget.attrs['disabled']
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        instance = self.instance
        
        # Limpiar el código
        if codigo:
            codigo = codigo.strip()
        
        # Si es una actualización y ya tenía código (no vacío)
        if instance and instance.pk and instance.codigo and instance.codigo.strip():
            # No permitir cambios si el código existente no está vacío
            if codigo != instance.codigo:
                raise forms.ValidationError("No se puede modificar el código porque ya tiene un valor asignado.")
            return codigo
        
        # Si es nuevo o no tenía código, validar que no esté vacío
        if not codigo:
            raise forms.ValidationError("El código es obligatorio para nuevos insumos.")
        
        # Validar unicidad
        queryset = InsumosOtros.objects.all()
        if instance and instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.filter(codigo=codigo).exists():
            raise forms.ValidationError("Ya existe un insumo con este código.")
        
        return codigo
    
    def clean_costo(self):
        costo = self.cleaned_data.get('costo')
        if costo is None:
            return 0
        if costo < 0:
            raise forms.ValidationError("El costo no puede ser negativo.")
        return costo