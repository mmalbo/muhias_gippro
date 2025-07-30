from django import forms
from materia_prima.models import MateriaPrima
from adquisiciones.models import Adquisicion

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