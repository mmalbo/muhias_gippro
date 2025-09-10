from django import forms
from .models import Adquisicion
from materia_prima.models import MateriaPrima
from materia_prima.choices import obtener_tipos_materia_prima
from nomencladores.almacen.models import Almacen
from envase_embalaje.models import EnvaseEmbalaje
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from envase_embalaje.formato.models import Formato
from InsumosOtros.models import InsumosOtros 

""" Genérico para todos """
class CompraForm(forms.ModelForm):
    class Meta:
        model = Adquisicion
        fields = ['fecha_compra', 'importada', 'factura']
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'importada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'factura': forms.FileInput(attrs={'class': 'form-control'}),
        }

""" Para materias primas """
class CantidadMateriasForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=20,
        label="¿Cuántas materias primas deseas registrar?",
        help_text="Máximo 20 materias por compra",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de materias primas'
        })
    )

class MateriaPrimaForm(forms.Form):
    EXISTING = 'existing'
    NEW = 'new'
    MATERIA_CHOICES = [
        (EXISTING, 'Usar materia prima existente'),
        (NEW, 'Registrar nueva materia prima')
    ]
    
    opcion = forms.ChoiceField(
        choices=MATERIA_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=EXISTING
    )
    
    materia_existente = forms.ModelChoiceField(
        queryset=MateriaPrima.objects.all(),
        required=False,
        label="Seleccionar materia prima existente",
        widget=forms.Select(attrs={'class': 'form-select materia-select'})
    )
    
    cantidad = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label="Cantidad adquirida",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        required=False,
        label="Almacen para su ubicación",
        widget=forms.Select(attrs={'class': 'form-select almacen-select'})
    )
    
    # Campos para nueva materia prima
    """ codigo = forms.CharField(
        max_length=20, 
        required=False, 
        label="Código",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    ) """
    nombre = forms.CharField(
        max_length=100, 
        required=False, 
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tipo_materia_prima = forms.ChoiceField(
        choices=obtener_tipos_materia_prima(),        
        required=True,
        initial='otros',
        label="Seleccionar tipo de materia prima",
        widget=forms.Select(attrs={'class': 'form-select tipo-materia-select'})
    )
    conformacion = forms.CharField(
        max_length=50, 
        required=False, 
        label="Conformación",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    unidad_medida = forms.CharField(
        max_length=255, 
        required=False, 
        label="Unidad de medida",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    concentracion = forms.IntegerField( 
        required=False, 
        label="Concentración",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    """ cantidad_almacen = forms.IntegerField( 
        required=False, 
        label="Cantidad en almacen",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    ) """
    costo = forms.FloatField(
        required=False,
        label="Costo",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    ficha_tecnica = forms.FileField(
        required=False,
        label= "Ficha Técnica",
        widget=forms.FileInput(attrs={'class': 'form-control'}) 
    )
    hoja_seguridad = forms.FileField(
        required=False,
        label= "Hoja de seguridad",
        widget=forms.FileInput(attrs={'class': 'form-control'}) 
    )
    
    def clean(self):
        cleaned_data = super().clean()
        opcion = cleaned_data.get('opcion')
        print(cleaned_data.get('nombre'))
        if opcion == self.EXISTING:
            if not cleaned_data.get('materia_existente'):
                self.add_error('materia_existente', 'Debes seleccionar una materia prima existente')
        elif opcion == self.NEW:
            if not cleaned_data.get('nombre'):
                self.add_error('nombre', 'El nombre es obligatorio para nuevas materias primas')
            """ if not cleaned_data.get('codigo'):
                self.add_error('codigo', 'El código es obligatorio para nuevas materias primas')
 """            
            # Validar que no exista una materia prima con el mismo nombre
            nombre = cleaned_data.get('nombre')
            #codigo = cleaned_data.get('codigo')
            if nombre and MateriaPrima.objects.filter(nombre=nombre).exists():
                self.add_error('nombre', 'Ya existe una materia prima con este nombre')
            """ if codigo and MateriaPrima.objects.filter(codigo=codigo).exists():
                self.add_error('codigo', 'Ya existe una materia prima con este código')
 """        
        return cleaned_data
    
""" Para envases y embalajes """
class CantidadEnvasesForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=20,
        label="¿Cuántos envases o embalajes deseas registrar?",
        help_text="Máximo 20 por compra",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de envases o embalajes'
        })
    )

class EnvasesForm(forms.Form):
    EXISTING = 'existing'
    NEW = 'new'
    ENVASE_CHOICES = [
        (EXISTING, 'Usar envase existente'),
        (NEW, 'Registrar nuevo envase o embalaje')
    ]
    
    opcion = forms.ChoiceField(
        choices=ENVASE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=EXISTING
    )
    
    envase_existente = forms.ModelChoiceField(
        queryset=EnvaseEmbalaje.objects.all(),
        required=False,
        label="Seleccionar envaseo embalaje existente",
        widget=forms.Select(attrs={'class': 'form-select materia-select'})
    )
    
    cantidad = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label="Cantidad adquirida",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        required=False,
        label="Almacen para su ubicación",
        widget=forms.Select(attrs={'class': 'form-select almacen-select'})
    )
    
    # Campos para nuevo envase
    tipo_envase_embalaje = forms.ModelChoiceField(
        queryset=TipoEnvaseEmbalaje.objects.all(),
        required=False,
        label="Seleccionar tipo de envase o embalaje",
        widget=forms.Select(attrs={'class': 'form-select tipo-envase-select'})
    )
    formato = forms.ModelChoiceField(
        queryset=Formato.objects.all(),
        required=False,
        label="Seleccionar formato",
        widget=forms.Select(attrs={'class': 'form-select formato-select'})
    )

    costo = forms.FloatField(
        required=False,
        label="Costo",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    
    def clean(self):
        cleaned_data = super().clean()
        opcion = cleaned_data.get('opcion')
        
        if opcion == self.EXISTING:
            if not cleaned_data.get('envase_existente'):
                self.add_error('envase_existente', 'Debes seleccionar un envase existente')
        elif opcion == self.NEW:
            if not cleaned_data.get('tipo_envase_embalaje'):
                self.add_error('tipo_envase_embalaje', 'El tipo de envase es obligatorio para nuevos evases o embalajes')
            if not cleaned_data.get('formato'):
                self.add_error('formato', 'El formato es obligatorio para nuevos eases o embalajes')
            
            """ # Validar que no exista una materia prima con el mismo nombre
            nombre = cleaned_data.get('nombre')
            codigo = cleaned_data.get('codigo')
            if nombre and MateriaPrima.objects.filter(nombre=nombre).exists():
                self.add_error('nombre', 'Ya existe una materia prima con este nombre')
            if codigo and MateriaPrima.objects.filter(codigo=codigo).exists():
                self.add_error('codigo', 'Ya existe una materia prima con este código') """
        
        return cleaned_data
    
""" Para insumos y otros """
class CantidadInsumosForm(forms.Form):
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=20,
        label="¿Cuántos insumos deseas registrar?",
        help_text="Máximo 20 por compra",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de insumos'
        })
    )

class InsumosForm(forms.Form):
    EXISTING = 'existing'
    NEW = 'new'
    INSUMOS_CHOICES = [
        (EXISTING, 'Usar insumo existente'),
        (NEW, 'Registrar nuevo insumo')
    ]
    
    opcion = forms.ChoiceField(
        choices=INSUMOS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=EXISTING
    )
    
    insumo_existente = forms.ModelChoiceField(
        queryset=InsumosOtros.objects.all(),
        required=False,
        label="Seleccionar insumo existente",
        widget=forms.Select(attrs={'class': 'form-select insumo-select'})
    )
    
    cantidad = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label="Cantidad adquirida",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        required=False,
        label="Almacen para su ubicación",
        widget=forms.Select(attrs={'class': 'form-select almacen-select'})
    )
    
    # Campos para nuevo insumo

    codigo = forms.CharField(
        max_length=20, 
        required=False, 
        label="Código",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    nombre = forms.CharField(
        max_length=255, 
        required=False, 
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    descripcion = forms.CharField(
        max_length=600, 
        required=False, 
        label="Descripción",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    costo = forms.FloatField(
        required=False,
        label="Costo",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    
    def clean(self):
        cleaned_data = super().clean()
        opcion = cleaned_data.get('opcion')
        
        if opcion == self.EXISTING:
            if not cleaned_data.get('insumo_existente'):
                self.add_error('insumo_existente', 'Debes seleccionar un insumo existente')
        elif opcion == self.NEW:
            if not cleaned_data.get('codigo'):
                self.add_error('codigo', 'El código es obligatorio para nuevos insumo')
            if not cleaned_data.get('nombre'):
                self.add_error('nombre', 'El nombre es obligatorio para nuevos insumos')
            
            # Validar que no exista un insumo con el mismo código o nombre
            nombre = cleaned_data.get('nombre')
            codigo = cleaned_data.get('codigo')
            if nombre and InsumosOtros.objects.filter(nombre=nombre).exists():
                self.add_error('nombre', 'Ya existe un insumo con este nombre')
            if codigo and InsumosOtros.objects.filter(codigo=codigo).exists():
                self.add_error('codigo', 'Ya existe un insumo con este código')
        
        return cleaned_data