from django import forms
from .models import Inv_Mat_Prima, Inv_Envase, Inv_Insumos, Inv_Producto
from nomencladores.models import Almacen

class AjusteInvMPForm(forms.ModelForm):
    causa = forms.CharField(
        max_length=100,
        required = False,
        label="Causa del ajuste",
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    
    class Meta:
        model = Inv_Mat_Prima
        fields = ['cantidad', 'almacen', 'materia_prima']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'almacen': forms.Select(attrs={'class': 'form-control'}),
            'materia_prima': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cantidad': 'Nueva cantidad',
        }
        

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['materia_prima'].disabled = True
        if self.user:
            if self.user.groups.filter(name='Presidencia-Admin').exists() or self.user.is_staff:
                self.fields['almacen'].queryset = Almacen.objects.all()
            else:
                almacen = Almacen.objects.filter(responsable=self.user).first()
                if almacen:
                    self.fields['almacen'].queryset = Almacen.objects.filter(id=almacen.id)
                    self.fields['almacen'].initial = almacen
                    self.fields['almacen'].disabled = True
                else:
                    self.fields['almacen'].queryset = Almacen.objects.none()

    def clean_causa(self):
        causa = self.cleaned_data.get('causa')
        if causa == '':
            raise forms.ValidationError("Debe especificar una causa del ajuste")
        return causa

class AjusteInvEEForm(forms.ModelForm):
    causa = forms.CharField(
        max_length=100,
        required = False,
        label="Causa del ajuste",
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    
    class Meta:
        model = Inv_Envase
        fields = ['cantidad', 'almacen', 'envase']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'almacen': forms.Select(attrs={'class': 'form-control'}),
            'envase': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cantidad': 'Nueva cantidad',
        }
        

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['envase'].disabled = True
        if self.user:
            if self.user.groups.filter(name='Presidencia-Admin').exists() or self.user.is_staff:
                self.fields['almacen'].queryset = Almacen.objects.all()
            else:
                almacen = Almacen.objects.filter(responsable=self.user).first()
                if almacen:
                    self.fields['almacen'].queryset = Almacen.objects.filter(id=almacen.id)
                    self.fields['almacen'].initial = almacen
                    self.fields['almacen'].disabled = True
                else:
                    self.fields['almacen'].queryset = Almacen.objects.none()

    def clean_causa(self):
        causa = self.cleaned_data.get('causa')
        if causa == '':
            raise forms.ValidationError("Debe especificar una causa del ajuste")
        return causa

class AjusteInvInsForm(forms.ModelForm):
    causa = forms.CharField(
        max_length=100,
        required = False,
        label="Causa del ajuste",
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    
    class Meta:
        model = Inv_Insumos
        fields = ['cantidad', 'almacen', 'insumos']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'almacen': forms.Select(attrs={'class': 'form-control'}),
            'insumos': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cantidad': 'Nueva cantidad',
        }
        

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['insumos'].disabled = True
        if self.user:
            if self.user.groups.filter(name='Presidencia-Admin').exists() or self.user.is_staff:
                self.fields['almacen'].queryset = Almacen.objects.all()
            else:
                almacen = Almacen.objects.filter(responsable=self.user).first()
                if almacen:
                    self.fields['almacen'].queryset = Almacen.objects.filter(id=almacen.id)
                    self.fields['almacen'].initial = almacen
                    self.fields['almacen'].disabled = True
                else:
                    self.fields['almacen'].queryset = Almacen.objects.none()

    def clean_causa(self):
        causa = self.cleaned_data.get('causa')
        if causa == '':
            raise forms.ValidationError("Debe especificar una causa del ajuste")
        return causa

class AjusteInvProdForm(forms.ModelForm):
    causa = forms.CharField(
        max_length=100,
        required = False,
        label="Causa del ajuste",
        widget=forms.TextInput(attrs={'class':'form-control'})
    )
    
    class Meta:
        model = Inv_Producto
        fields = ['cantidad', 'almacen', 'producto', 'lote']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'almacen': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cantidad': 'Nueva cantidad',
        }
        

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['producto'].disabled = True
        if self.user:
            if self.user.groups.filter(name='Presidencia-Admin').exists() or self.user.is_staff:
                self.fields['almacen'].queryset = Almacen.objects.all()
            else:
                almacen = Almacen.objects.filter(responsable=self.user).first()
                if almacen:
                    self.fields['almacen'].queryset = Almacen.objects.filter(id=almacen.id)
                    self.fields['almacen'].initial = almacen
                    self.fields['almacen'].disabled = True
                else:
                    self.fields['almacen'].queryset = Almacen.objects.none()

    def clean_causa(self):
        causa = self.cleaned_data.get('causa')
        if causa == '':
            raise forms.ValidationError("Debe especificar una causa del ajuste")
        return causa