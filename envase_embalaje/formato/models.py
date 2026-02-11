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

    capacidad = models.IntegerField(
        null=False,
        blank=False,
        default=0,
        verbose_name="Valor de capacidad",
    )

    class Meta:
        verbose_name = "Formato"
        verbose_name_plural = "Formatos"

    def __str__(self):
        return f"{self.capacidad} {self.unidad_medida}" if self.capacidad > 0 else "A granel"
    
    def __unicode__(self):
        return f"{self.capacidad} {self.unidad_medida}"

    def clean(self):
        if self.capacidad and not str(self.capacidad).isdigit():
            raise ValidationError("El campo 'capacidad' debe ser un entero.")
        super().clean()
