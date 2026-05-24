from django import forms

from envase_embalaje.formato.models import Formato
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from nomencladores.almacen.models import Almacen
from .models import EnvaseEmbalaje
from django.apps import apps

class EnvaseEmbalajeForm(forms.ModelForm):
    tipo_envase_embalaje = forms.ModelChoiceField(queryset=TipoEnvaseEmbalaje.objects.all(),
                                                  label='Tipo de envase o embalaje',
                                                  widget=forms.Select(attrs={'class': 'form-control'})
                                                  )
    formato = forms.ModelChoiceField(queryset=Formato.objects.all(),
                                     label='Formato',
                                     widget=forms.Select(attrs={'class': 'form-control'})
                                     )
    """almacen = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Almacenes'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Almacen = apps.get_model('almacen', 'Almacen')
        self.fields['almacen'].queryset = Almacen.objects.all()"""

    class Meta:
        model = EnvaseEmbalaje
        fields = [
            # 'codigo_envase',
            'nombre',
            'tipo_envase_embalaje',
            'formato',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            #'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre identificativo del envase'
            # 'codigo_envase': 'Código de envace:',
            # 'cantidad': 'Cantidad:',
        }


class EnvaseEmbalajeUpdateForm(forms.ModelForm):
    tipo_envase_embalaje = forms.ModelChoiceField(
        queryset=TipoEnvaseEmbalaje.objects.all(),
        label='Tipo de envase o embalaje',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    formato = forms.ModelChoiceField(
        queryset=Formato.objects.all(),
        label='Formato',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # Permitir nulo ya que blank=True en el modelo
    )
    
    class Meta:
        model = EnvaseEmbalaje
        fields = [
            'codigo_envase',
            'tipo_envase_embalaje',
            'formato',
            'nombre',
            'proveedor',
            'costo',
        ]
        widgets = {
            'codigo_envase': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'codigo_envase': 'Codigo:',
            'nombre': 'Nombre:',
            'proveedor': 'Proveedor:',
            'costo': 'Costo:',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el objeto ya existe Y tiene un código válido, entonces hacerlo readonly
        if self.instance and self.instance.pk and self.instance.codigo_envase:
            self.fields['codigo_envase'].widget.attrs['readonly'] = 'readonly'
            self.fields['codigo_envase'].help_text = "El codigo no puede modificarse porque ya tiene un valor asignado"
        else:
            # Si es nuevo o el código está vacío, permitir edición
            self.fields['codigo_envase'].required = True
            self.fields['codigo_envase'].help_text = "Ingrese un codigo único para este envase/embalaje"
            
        # Hacer que el campo nombre sea opcional si quieres mantener el valor por defecto
        self.fields['nombre'].required = False
        self.fields['proveedor'].required = False
        self.fields['costo'].required = False

    def clean_codigo_envase(self):
        codigo = self.cleaned_data.get('codigo_envase')
        instance = self.instance
        
        # Si es una actualización y ya tenía código, no permitir cambios
        if instance and instance.pk and instance.codigo_envase:
            if codigo != instance.codigo_envase:
                raise forms.ValidationError("No se puede modificar el codigo porque ya tiene un valor asignado.")
            return codigo
        
        # Si es nuevo o no tenía código, validar unicidad
        if EnvaseEmbalaje.objects.exclude(pk=instance.pk if instance else None).filter(codigo_envase=codigo).exists():
            raise forms.ValidationError("Ya existe un envase/embalaje con este codigo.")
        
        return codigo
    