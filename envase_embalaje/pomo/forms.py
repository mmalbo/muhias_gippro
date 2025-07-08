from django import forms
from .models import Pomo
from nomencladores.color.models import Color


class PomoForm(forms.ModelForm):
    color = forms.ModelChoiceField(queryset=Color.objects.all(),
                                   label='Color',
                                   widget=forms.Select(attrs={'class': 'form-control'})
                                   )

    class Meta:
        model = Pomo
        # fields = ['codigo','nombre','forma','material', 'color']
        fields = ['nombre','forma','material', 'color']
        widgets = {
            # 'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'forma': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            # 'codigo': 'Código',
            'nombre': 'Nombre',
            'forma': 'Forma',
            'material': 'Material',
        }

class UpdatePomoForm(forms.ModelForm):
    color = forms.ModelChoiceField(queryset=Color.objects.all(),
                                   label='Color',
                                   widget=forms.Select(attrs={'class': 'form-control'})
                                   )

    class Meta:
        model = Pomo
        fields = ['codigo','nombre','forma','material', 'color']
        # fields = ['nombre','forma','material', 'color']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'forma': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'forma': 'Forma',
            'material': 'Material',
        }
