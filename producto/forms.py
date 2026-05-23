from django import forms

from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen
from .models import Producto


class ProductoForm(forms.ModelForm):
    
    class Meta:
        model = Producto
        fields = [
            'codigo_producto',
            'codigo_3l',
            'nombre_comercial',
            'costo',
            'prod_base',
            'ficha_costo',
            'ficha_tecnica_folio',
        ]
        labels = {
            'codigo_producto': 'Código del producto',
            'codigo_3l': 'Código de 3 letras',
            'nombre_comercial': 'Nombre comercial',
            'costo': 'Costo ($)',
            'prod_base': '¿Es producto base?',
            'ficha_costo': 'Ficha de costo',
            'ficha_tecnica_folio': 'Ficha técnica folio',
        }
        widgets = {
            'codigo_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_3l': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prod_base': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ficha_costo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'ficha_tecnica_folio': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        help_texts = {
            'codigo_producto': 'Código único del producto (opcional, se puede asignar después)',
            'codigo_3l': 'Código de 3 letras para identificación rápida (ej: ABC)',
            'costo': 'Costo del producto',
            'prod_base': 'Marque si este producto es base para otros productos',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos opcionales
        self.fields['codigo_producto'].required = False
        self.fields['codigo_3l'].required = False
        self.fields['costo'].required = False
        self.fields['prod_base'].required = False
        
        # Lógica para el campo código_producto
        instance = self.instance
        if instance and instance.pk and instance.codigo_producto and instance.codigo_producto.strip():
            # Si ya tiene un código válido, hacerlo readonly
            self.fields['codigo_producto'].widget.attrs['readonly'] = 'readonly'
            self.fields['codigo_producto'].widget.attrs['class'] = 'form-control bg-light'
            self.fields['codigo_producto'].help_text = "El código no puede modificarse porque ya tiene un valor asignado"
        else:
            # Si es nuevo o el código está vacío, permitir edición
            self.fields['codigo_producto'].required = False
            self.fields['codigo_producto'].widget.attrs['readonly'] = False
            self.fields['codigo_producto'].help_text = "Ingrese un código único para este producto (opcional, puede asignarse después)"
            if 'disabled' in self.fields['codigo_producto'].widget.attrs:
                del self.fields['codigo_producto'].widget.attrs['disabled']
        
        # Mostrar archivos actuales si existen
        if instance and instance.pk:
            if instance.ficha_tecnica_folio:
                self.fields['ficha_tecnica_folio'].help_text = f'Archivo actual: {instance.get_ficha_tecnica_folio_name()}'
            if instance.ficha_costo:
                self.fields['ficha_costo'].help_text = f'Archivo actual: {instance.get_ficha_costo_name()}'
    
    def clean_codigo_producto(self):
        codigo = self.cleaned_data.get('codigo_producto')
        instance = self.instance
        
        # Limpiar el código
        if codigo:
            codigo = codigo.strip()
        else:
            codigo = None
        
        # Si es una actualización y ya tenía código (no vacío)
        if instance and instance.pk and instance.codigo_producto and instance.codigo_producto.strip():
            # No permitir cambios si el código existente no está vacío
            if codigo != instance.codigo_producto:
                raise forms.ValidationError("No se puede modificar el código porque ya tiene un valor asignado.")
            return codigo
        
        # Si es nuevo o no tenía código, validar unicidad si se proporciona un código
        if codigo:
            queryset = Producto.objects.all()
            if instance and instance.pk:
                queryset = queryset.exclude(pk=instance.pk)
            
            if queryset.filter(codigo_producto=codigo).exists():
                raise forms.ValidationError("Ya existe un producto con este código.")
        
        return codigo
    
    def clean_codigo_3l(self):
        codigo_3l = self.cleaned_data.get('codigo_3l')
        if codigo_3l:
            codigo_3l = codigo_3l.strip().upper()
            if len(codigo_3l) > 3:
                raise forms.ValidationError("El código de 3 letras no puede tener más de 3 caracteres.")
        return codigo_3l
    
    def clean_costo(self):
        costo = self.cleaned_data.get('costo')
        if costo is not None and costo < 0:
            raise forms.ValidationError("El costo no puede ser negativo.")
        return costo