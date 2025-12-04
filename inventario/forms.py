from django import forms
from .models import Inv_Mat_Prima
from nomencladores.models import Almacen

class AjusteInvMPForm(forms.ModelForm):

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
            if self.user.groups.filter(name='Presidencia-Admin').exists():
                self.fields['almacen'].queryset = Almacen.objects.all()
            else:
                almacen = Almacen.objects.filter(responsable=self.user).first()
                if almacen:
                    self.fields['almacen'].queryset = Almacen.objects.filter(id=almacen.id)
                    self.fields['almacen'].initial = almacen
                    self.fields['almacen'].disabled = True
                else:
                    self.fields['almacen'].queryset = Almacen.objects.none()