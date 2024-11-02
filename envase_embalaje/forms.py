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
                                       label='Capacidad',
                                       widget=forms.Select(attrs={'class': 'form-control'})
                                       )

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
        model = EnvaseEmbalaje
        fields = [
            'codigo_envase',
            'cantidad',
            'tipo_envase_embalaje',
            'formato',
            'almacen',
        ]
        widgets = {
            'codigo_envase': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'codigo_envase': 'Código de envace:',
            'cantidad': 'Cantidad:',
        }
