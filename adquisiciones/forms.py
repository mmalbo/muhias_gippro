from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import MateriaPrimaAdquisicion, EnvaseAdquisicion, InsumosAdquisicion


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
