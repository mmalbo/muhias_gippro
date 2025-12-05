# forms.py
from django.utils import timezone
from django import forms

from materia_prima.models import MateriaPrima
from nomencladores.planta.models import Planta
from nomencladores.almacen.models import Almacen
from .models import Produccion, Prod_Inv_MP, PruebaQuimica, DetallePruebaQuimica, ParametroPrueba
from producto.models import Producto
from envase_embalaje.formato.models import Formato
from .choices import TIPOS_PARAMETRO

class ProductoRapidoForm(forms.ModelForm):
    """Form para crear producto rápido desde producción"""
    class Meta:
        model = Producto
        fields = ['nombre_comercial']
        widgets = {
            'nombre_comercial': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del nuevo producto...'
            }),            
        }

class ProduccionForm(forms.ModelForm):
    planta = forms.ModelChoiceField( queryset=Planta.objects.all(), 
                                    widget=forms.Select(attrs={'class': 'form-control'}), required=True)

    # Campo para seleccionar producto existente
    catalogo_producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        label="Seleccionar Producto Existente",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Seleccione un producto del catálogo"
    )

    # Campo para crear nuevo producto
    nuevo_producto_nombre = forms.CharField(
        required=False,
        max_length=200,
        label="O Crear Nuevo Producto",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del nuevo producto...'
        }),
        help_text="Si el producto no existe en el catálogo, ingrese el nombre aquí"
    )
    
    class Meta:
        model = Produccion
        fields = ['lote', 'cantidad_estimada', 'costo', 'planta', 'prod_result']
        widgets = {
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_estimada': forms.NumberInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prod_result': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            #'planta': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener formato a granel por defecto
        formato_agranel = Formato.objects.filter(capacidad=0).first()

    def clean(self):
        cleaned_data = super().clean()
        catalogo_producto = cleaned_data.get('catalogo_producto')
        nuevo_producto_nombre = cleaned_data.get('nuevo_producto_nombre')
        
        # Validar que se seleccione un producto existente o se cree uno nuevo
        if not catalogo_producto and not nuevo_producto_nombre:
            raise forms.ValidationError(
                "Debe seleccionar un producto existente o ingresar el nombre de un nuevo producto"
            )
        
        # Validar que no se hagan ambas cosas
        if catalogo_producto and nuevo_producto_nombre:
            raise forms.ValidationError(
                "Solo puede seleccionar un producto existente O crear uno nuevo, no ambas opciones"
            )
        
        # Validar que el nuevo producto no exista ya
        if nuevo_producto_nombre:
            if Producto.objects.filter(nombre_comercial__iexact=nuevo_producto_nombre.strip()).exists():
                raise forms.ValidationError(
                    f"El producto '{nuevo_producto_nombre}' ya existe en el catálogo. Por favor selecciónelo de la lista."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        # Primero crear el producto si es necesario
        nuevo_producto_nombre = self.cleaned_data.get('nuevo_producto_nombre')
        if nuevo_producto_nombre:            
            # Crear nuevo producto en el catálogo
            catalogo_producto = Producto.objects.create(
                nombre=nuevo_producto_nombre.strip(),
                formato_default=Formato.objects.filter(capacidad=0).first()
                #self.formato_agranel
            )
            self.instance.catalogo_producto = catalogo_producto
        else:
            self.instance.catalogo_producto = self.cleaned_data['catalogo_producto']
        
        return super().save(commit)

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
        fields = ['pruebas_quimicas_ext', 'prod_conform']
        widgets = {
            'pruebas_quimicas_ext': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            }),
            'prod_conform': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'pruebas_quimicas_ext': 'Archivo de Pruebas (PDF, Excel, Imagen, etc.)',
            'prod_conform': 'Producto conforme'
        }
    
    def clean_archivo_pruebas(self):
        archivo = self.cleaned_data.get('pruebas_quimicas_ext')
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
            
class ParametroPruebaForm(forms.ModelForm):
    class Meta:
        model = ParametroPrueba
        fields = [
            'nombre', 'tipo', 'unidad_medida', 'descripcion', 'metodo_ensayo', 
            'valor_minimo', 'valor_maximo', 'valor_objetivo', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'metodo_ensayo': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001'
            }),
            'valor_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001'
            }),
            'valor_objetivo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001'
            }),
        }
 
    def clean(self):
        cleaned_data = super().clean()
        valor_minimo = cleaned_data.get('valor_minimo')
        valor_maximo = cleaned_data.get('valor_maximo')
        
        # Validar que mínimo sea menor que máximo
        if valor_minimo and valor_maximo and valor_minimo >= valor_maximo:
            raise forms.ValidationError(
                "El valor mínimo debe ser menor que el valor máximo"
            )
        
        return cleaned_data

class BuscarParametroForm(forms.Form):
    """Formulario para buscar y filtrar parámetros"""
    tipo = forms.ChoiceField(
        choices=[('', 'Todos')] + TIPOS_PARAMETRO,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    activo = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código o nombre...'
        })
    )

class PruebaQuimicaForm(forms.ModelForm):
    class Meta:
        model = PruebaQuimica
        fields = ['fecha_vencimiento', 'observaciones', 'archivo_resultado']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones generales de la prueba...'
            }),
            'archivo_resultado': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png'
            })
        }

class DetallePruebaForm(forms.ModelForm):
    class Meta:
        model = DetallePruebaQuimica
        fields = ['parametro', 'valor_medido', 'observaciones']
        widgets = {
            'parametro': forms.Select(attrs={'class': 'form-control'}),
            'valor_medido': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'observaciones': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones específicas...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar parámetros activos
        self.fields['parametro'].queryset = ParametroPrueba.objects.filter(activo=True)

class AprobarPruebaForm(forms.Form):
    observaciones_aprobacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones de la aprobación...'
        })
    )

DetallePruebaFormSet = forms.inlineformset_factory(
    PruebaQuimica,
    DetallePruebaQuimica,
    form=DetallePruebaForm,
    extra=5,  # Número de forms vacíos a mostrar
    can_delete=True
)