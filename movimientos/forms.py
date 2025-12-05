from django import forms
from materia_prima.models import MateriaPrima
from adquisiciones.models import Adquisicion
from .models import Vale_Movimiento_Almacen

class RecepcionMateriaPrimaForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=MateriaPrima.objects.none(),
        label="Seleccionar materia prima"
    )
    cantidad = forms.FloatField(
        label="Cantidad recibida",
        widget=forms.NumberInput(attrs={'step': '0.10'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener el grupo de vendedores
        """ producto = Group.objects.filter(name='vendedores').first()
        
        if vendedores_group:
            # Filtrar usuarios que pertenecen al grupo
            self.fields['seller'].queryset = User.objects.filter(groups=vendedores_group)
        else:
            # Si el grupo no existe, mostrar usuarios vacíos
            self.fields['seller'].queryset = User.objects.none()
        
        # Opcional: ordenar por nombre completo
        self.fields['seller'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})" """

class MovimientoFormUpdate(forms.ModelForm):

    class Meta:
        model = Vale_Movimiento_Almacen
        fields = [ 'tipo', 'consecutivo', 'almacen',
                  'suministrador', 'transportista', 'chapa']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'consecutivo': forms.NumberInput(attrs={'class': 'form-control'}),
            'almacen': forms.Select(attrs={'class': 'form-control'}),
            'suministrador': forms.TextInput(attrs={'class': 'form-control'}),
            'transportista': forms.TextInput(attrs={'class': 'form-control-file'}),
            'chapa': forms.TextInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f'self.instance{self.instance.tipo}')
        self.fields['tipo'].initial = self.instance.tipo 
   