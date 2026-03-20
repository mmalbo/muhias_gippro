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
        # fields = ['codigo','nombre', 'color']
        fields = ['nombre', 'color', 'material']
        widgets = {
            # 'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            # 'codigo': 'Código',
            'nombre': 'Nombre',
            'material': 'Material'
        }


class UpdateTanqueForm(forms.ModelForm):
    color = forms.ModelChoiceField(
        queryset=Color.objects.all(),
        label='Color',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Tanque
        fields = ['nombre', 'color', 'material']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre',
            'material': 'Material'
        }
