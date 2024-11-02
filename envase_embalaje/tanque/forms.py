from django import forms
from .models import Tanque
from nomencladores.color.models import Color


class TanqueForm(forms.ModelForm):
    color = forms.ModelChoiceField(queryset=Color.objects.all(),
                                   label='Color',
                                   widget=forms.Select(attrs={'class': 'form-control'})
                                   )

    class Meta:
        model = Tanque
        fields = ['codigo','nombre', 'color']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
        }
