from django import forms
from .models import Pomo
from nomencladores.color.models import Color


class PomoForm(forms.ModelForm):
    color_input = forms.CharField(
        label="Color",
        widget=forms.TextInput(attrs={
            'list': 'colores-list',
            'autocomplete': 'off',
            'class': 'form-control'
        })
    )
    """ color = forms.ModelChoiceField(queryset=Color.objects.all(),
                                   label='Color',
                                   widget=forms.Select(attrs={'class': 'form-control'})
                                   ) """

    class Meta:
        model = Pomo
        fields = ['nombre','forma','material']
        """ widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'forma': forms.TextInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre',
            'forma': 'Forma',
            'material': 'Material',
        } """
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colores = Color.objects.all().values_list('nombre', flat=True)
        
        # Valor inicial si es edición
        if self.instance and self.instance.pk and hasattr(self.instance, 'color'):
            self.fields['color_input'].initial = self.instance.colore
        
    
    def clean_color_input(self):
        nombre_color = self.cleaned_data['color_input'].strip()
        
        # Validar que no esté vacío
        if not nombre_color:
            raise forms.ValidationError("Debe especificar un color")
            
        # Crear o obtener el color
        color, created = Color.objects.get_or_create(
            nombre__iexact=nombre_color,
            defaults={'nombre': nombre_color}
        )
        return color

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
