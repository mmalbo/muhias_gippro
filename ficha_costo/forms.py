from django import forms
from .models import FichaCosto, CHOICE_MONEDAS

class FichaCostoForm(forms.ModelForm):
    """
    Formulario para crear y editar fichas de costo
    """
    
    class Meta:
        model = FichaCosto
        fields = ['costo_x_itro', 'utilidad', 'monto_cambio', 'activo']
        widgets = {
            'costo_x_itro': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'utilidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.30'
            }),
            'monto_cambio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1.00'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'costo_x_itro': 'Costo por litro',
            'utilidad': 'Utilidad (%)',
            'monto_cambio': 'Cambio de referencia',
            'activo': 'Ficha activa',
        }
        help_texts = {
            'utilidad': 'Valor entre 0 y 1 (ej: 0.30 = 30%)',
            'monto_cambio': 'Valor de referencia para conversión de moneda',
        }
    
    def clean_utilidad(self):
        """Validar que la utilidad esté entre 0 y 1"""
        utilidad = self.cleaned_data.get('utilidad')
        if utilidad < 0 or utilidad > 1:
            raise forms.ValidationError('La utilidad debe estar entre 0 y 1')
        return utilidad
    
    def clean_costo_x_itro(self):
        """Validar que el costo sea positivo"""
        costo = self.cleaned_data.get('costo_x_itro')
        if costo <= 0:
            raise forms.ValidationError('El costo por litro debe ser mayor que 0')
        return costo
    
    def clean_monto_cambio(self):
        """Validar que el monto de cambio sea positivo"""
        monto = self.cleaned_data.get('monto_cambio')
        if monto <= 0:
            raise forms.ValidationError('El monto de cambio debe ser mayor que 0')
        return monto

class FichaCostoFilterForm(forms.Form):
    """
    Formulario para filtrar fichas de costo
    """
    # Filtro por mes (año-mes)
    mes = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    activo = forms.ChoiceField(
        choices=[('', 'Todos'), ('True', 'Activos'), ('False', 'Inactivos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generar opciones de meses dinámicamente
        from .models import FichaCosto
        meses = FichaCosto.objects.dates('fecha_creacion', 'month', order='DESC')
        choices = [('', 'Todos los meses')]
        for fecha in meses:
            mes_nombre = fecha.strftime('%B %Y')
            mes_codigo = fecha.strftime('%Y-%m')
            choices.append((mes_codigo, mes_nombre))
        self.fields['mes'].choices = choices