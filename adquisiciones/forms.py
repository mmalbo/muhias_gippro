from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from .models import MateriaPrimaAdquisicion
#, EnvaseAdquisicion, InsumosAdquisicion


class MateriaPrimaAdquisicionForm(forms.ModelForm):
    class Meta:
        model = MateriaPrimaAdquisicion
        fields = ['fecha_compra', 'factura', 'importada', 'cantidad', 'materia_prima']
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'factura': forms.FileInput(attrs={'class': 'form-control'}),  # Cambiado a FileInput
            'importada': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:70%'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'materia_prima': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'fecha_compra': 'Fecha de la compra',
            'factura': 'Factura',
            'importada': 'Es importada',
            'cantidad': 'Cantidad',
            'materia_prima': 'Materia prima',
        }

    def clean_fecha_compra(self):
        fecha_compra = self.cleaned_data.get('fecha_compra')
        if fecha_compra and fecha_compra > timezone.now():
            raise ValidationError("La fecha de compra no puede ser mayor que la fecha actual.")
        return fecha_compra

    def clean_factura(self):
        factura = self.cleaned_data.get('factura')
        if factura:
            # Validar el tipo de archivo
            if not (factura.name.endswith('.pdf') or
                    factura.name.endswith('.jpg') or
                    factura.name.endswith('.jpeg') or
                    factura.name.endswith('.png')):
                raise ValidationError("El archivo debe ser un PDF o una imagen (JPG, JPEG, PNG).")

            # Validar el tamaño del archivo
            if factura.size > 1 * 1024 * 1024:  # 1 MB
                raise ValidationError("El tamaño del archivo no puede ser mayor a 1 MB.")

        return factura

"""
class EnvaseAdquisicionForm(forms.ModelForm):
    class Meta:
        model = EnvaseAdquisicion
        fields = ['fecha_compra', 'factura', 'importada', 'cantidad', 'envase']
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'factura': forms.FileInput(attrs={'class': 'form-control'}),  # Cambiado a FileInput
            'importada': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:70%'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'envase': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'fecha_compra': 'Fecha de la compra',
            'factura': 'Factura',
            'importada': 'Es importada',
            'cantidad': 'Cantidad',
            'envase': 'Envase',
        }

    def clean_fecha_compra(self):
        fecha_compra = self.cleaned_data.get('fecha_compra')
        if fecha_compra and fecha_compra > timezone.now():
            raise ValidationError("La fecha de compra no puede ser mayor que la fecha actual.")
        return fecha_compra

    def clean_factura(self):
        factura = self.cleaned_data.get('factura')
        if factura:
            # Validar el tipo de archivo
            if not (factura.name.endswith('.pdf') or
                    factura.name.endswith('.jpg') or
                    factura.name.endswith('.jpeg') or
                    factura.name.endswith('.png')):
                raise ValidationError("El archivo debe ser un PDF o una imagen (JPG, JPEG, PNG).")

            # Validar el tamaño del archivo
            if factura.size > 1 * 1024 * 1024:  # 1 MB
                raise ValidationError("El tamaño del archivo no puede ser mayor a 1 MB.")

        return factura


class InsumosAdquisicionForm(forms.ModelForm):
    class Meta:
        model = InsumosAdquisicion
        fields = ['fecha_compra', 'factura', 'importada', 'cantidad', 'insumo']
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'factura': forms.FileInput(attrs={'class': 'form-control'}),  # Cambiado a FileInput
            'importada': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'right:70%'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'insumo': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'fecha_compra': 'Fecha de la compra',
            'factura': 'Factura',
            'importada': 'Es importada',
            'cantidad': 'Cantidad',
            'insumo': 'Insumos y otros',
        }

    def clean_fecha_compra(self):
        fecha_compra = self.cleaned_data.get('fecha_compra')
        if fecha_compra and fecha_compra > timezone.now():
            raise ValidationError("La fecha de compra no puede ser mayor que la fecha actual.")
        return fecha_compra

    def clean_factura(self):
        factura = self.cleaned_data.get('factura')
        if factura:
            # Validar el tipo de archivo
            if not (factura.name.endswith('.pdf') or
                    factura.name.endswith('.jpg') or
                    factura.name.endswith('.jpeg') or
                    factura.name.endswith('.png')):
                raise ValidationError("El archivo debe ser un PDF o una imagen (JPG, JPEG, PNG).")

            # Validar el tamaño del archivo
            if factura.size > 1 * 1024 * 1024:  # 1 MB
                raise ValidationError("El tamaño del archivo no puede ser mayor a 1 MB.")

        return factura
"""

class PasoAdquisicionForm(forms.Form):
    fecha_compra = forms.DateTimeField(
        label="Fecha de compra",
        initial=timezone.now,
        required=True,
        widget=forms.DateInput(attrs={'type': 'date-local'})
    )
    factura = forms.FileField(
        label="Factura",
        required=False
    )
    importada = forms.BooleanField(
        label="¿Es importada?",
        required=False
    )
    cantidad = forms.IntegerField(
        label="Cantidad de elementos",
        min_value=1,
        required=True,
        initial=1
    )

    def clean(self):
        cleaned_data = super().clean()
        if not self.is_valid():  # Verificación explícita
            raise ValidationError("Por favor completa todos los campos requeridos")
        return cleaned_data

    def clean_fecha_compra(self):
        fecha_compra = self.cleaned_data.get('fecha_compra')
        if fecha_compra and fecha_compra > timezone.now():
            raise ValidationError("La fecha de compra no puede ser mayor que la fecha actual.")
        return fecha_compra

    def clean_factura(self):
        factura = self.cleaned_data.get('factura')
        if factura:
            # Validar el tipo de archivo
            if not (factura.name.endswith('.pdf') or
                    factura.name.endswith('.jpg') or
                    factura.name.endswith('.jpeg') or
                    factura.name.endswith('.png')):
                raise ValidationError("El archivo debe ser un PDF o una imagen (JPG, JPEG, PNG).")

            # Validar el tamaño del archivo
            if factura.size > 5 * 1024 * 1024:  # 1 MB
                raise ValidationError("El tamaño del archivo no puede ser mayor a 1 MB.")

        return factura


class PasoMateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrimaAdquisicion
        fields = ['materia_prima','cant_mat_prim']
        widgets = {
            'materia_prima': forms.Select(attrs={'class': 'form-select'})
        }

