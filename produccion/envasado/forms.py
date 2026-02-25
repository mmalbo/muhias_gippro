# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import *
from producto.models import Producto
from inventario.models import *
from envase_embalaje.models import *

class SolicitudEnvasadoForm(forms.ModelForm):
    class Meta:
        model = SolicitudEnvasado
        fields = [
            'lote_produccion_origen', 'cantidad_solicitada',
            'fecha_inicio', 'observaciones'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                #'min': timezone.now().date().isoformat()
            }),
            'observaciones': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Observaciones generales de la solicitud...'
            }),
            'lote_produccion_origen': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_solicitada': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
        }
        labels = {
            'lote_produccion_origen': 'Lote de producción a envasar',
            'cantidad_solicitada': 'Cantidad a envasar (L/kg)',
            'fecha_inicio': 'Fecha estimada de inicio',
            'observaciones': 'Observaciones',
        }

    # Campos para manejar datos dinámicos
    envases = forms.CharField(widget=forms.HiddenInput(), required=False)
    insumos = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar lotes con cantidad disponible
        self.fields['lote_produccion_origen'].queryset = Inv_Producto.objects.filter(
            cantidad__gt=0 ).select_related('producto', 'almacen').order_by('lote_produccion')

    def clean_cantidad_solicitada(self):
        cantidad = self.cleaned_data.get('cantidad_solicitada')
        if cantidad and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero')
        return cantidad

    def clean(self):
        cleaned_data = super().clean()
        lote = cleaned_data.get('lote_produccion_origen')
        cantidad = cleaned_data.get('cantidad_solicitada')
        envases_data = cleaned_data.get('envases')
        insumos_data = cleaned_data.get('insumos')

        # Validar disponibilidad en inventario
        if lote and cantidad:
            if lote.cantidad < cantidad:
                raise ValidationError({
                    'cantidad_solicitada': f'El lote {lote.lote_produccion} solo tiene {lote.cantidad} disponibles'
                })

        # Validar que haya al menos un envase
        if envases_data:
            import json
            try:
                envases = json.loads(envases_data)
                if not envases:
                    raise ValidationError('Debe agregar al menos un envase')
            except json.JSONDecodeError:
                raise ValidationError('Error en datos de envases')
        else:
            raise ValidationError('Debe agregar al menos un envase')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.solicitante = self.user
        
        if commit:
            instance.save()
            
            # Procesar envases
            if self.cleaned_data.get('envases'):
                import json
                envases = json.loads(self.cleaned_data['envases'])
                for envase_data in envases:
                    DetalleEnvasado.objects.create(
                        solicitud=instance,
                        presentacion_id=envase_data['id'],
                        cantidad_unidades=envase_data['cantidad']
                    )
            
            # Procesar insumos
            if self.cleaned_data.get('insumos'):
                import json
                insumos = json.loads(self.cleaned_data['insumos'])
                for insumo_data in insumos:
                    ConsumoInsumoEnvasado.objects.create(
                        solicitud=instance,
                        insumo_id=insumo_data['id'],
                        cantidad_unidades=insumo_data['cantidad']
                    )
        
        return instance

class LoteEnvasadoForm(forms.ModelForm):
    class Meta:
        model = SolicitudEnvasado
        fields = ['unidades_producidas', 'fecha_vencimiento', 'observaciones']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.solicitud = kwargs.pop('solicitud')
        super().__init__(*args, **kwargs)        
    
    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad_producida')
        
        if cantidad:
            # Validar que no se exceda la cantidad solicitada
            detalle = DetalleEnvasado.objects.get(
                solicitud=self.solicitud,
            )

            if cantidad > detalle.cantidad_unidades:
                raise ValidationError(
                    f'La cantidad excede lo solicitado. '
                    f'Restante: {detalle.cantidad_unidades - cantidad}'
                )
        
        return cleaned_data