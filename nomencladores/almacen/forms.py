from django import forms
from .models import Almacen
from django.apps import apps

class AlmacenForm(forms.ModelForm):
    materias_primas = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'width:100%'}),
        required=False,
        label='Materias Primas'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MateriaPrima = apps.get_model('materia_prima', 'MateriaPrima')
        self.fields['materias_primas'].queryset = MateriaPrima.objects.all()

    class Meta:
        model = Almacen
        fields = [
            'nombre',
            'ubicacion',
            'propio',
            'materias_primas',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'propio': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:80%'}),
        }
        labels = {
            'nombre': 'Nombre:',
            'ubicacion': 'Ubicación:',
            'propio': 'Propio:',
        }
