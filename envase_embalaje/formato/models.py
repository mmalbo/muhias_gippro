from django.core.exceptions import ValidationError
from django.db import models
from bases.bases.models import ModeloBase


class Formato(ModeloBase):
    unidad_medida = models.TextField(
        null=False,
        blank=False,
        max_length=255,
        verbose_name="Unidad de medida",
    )

    capacidad = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=False,
        blank=False,
        default=0,
        verbose_name="Valor de capacidad",
    )

    class Meta:
        verbose_name = "Formato"
        verbose_name_plural = "Formatos"

    def __str__(self):
        return f"{self.capacidad}{self.unidad_medida}" if self.capacidad > 0 else "AG"
    
    def __unicode__(self):
        return f"{self.capacidad}{self.unidad_medida}" if self.capacidad > 0 else "AG"
    
    @property
    def volumen(self):
        if self.unidad_medida.lower() in ['ml', 'g']:
            return self.capacidad / 1000        
        if self.unidad_medida.lower() in ['l', 'kg']:
            return self.capacidad if self.capacidad > 0 else 1
        return 0
    

    """def clean(self):
        if self.capacidad and not str(self.capacidad).isdigit():
            raise ValidationError("El campo 'capacidad' debe ser un entero.")
        super().clean()"""
