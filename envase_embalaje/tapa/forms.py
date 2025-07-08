from django import forms
from .models import Tapa
from nomencladores.color.models import Color


class TapaForm(forms.ModelForm):
    color = forms.ModelChoiceField(queryset=Color.objects.all(),
                                   label='Color',
                                   widget=forms.Select(attrs={'class': 'form-control'})
                                   )

    class Meta:
        model = Tapa
        fields = ['nombre', 'color', 'descripcion',]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            #'material': forms.TextInput(attrs={'class': 'form-control'}),

        }
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            #'material': 'Material',
        }


class UpdateTapaForm(forms.ModelForm):
    color = forms.ModelChoiceField(
        queryset=Color.objects.all(),
        label='Color',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Tapa
        fields = ['codigo', 'nombre', 'color', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            #'material': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            #'material': 'Material',
        }
