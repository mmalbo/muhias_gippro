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
        verbose_name="Unidad de medida",
    )

    class Meta:
        verbose_name = "Unidad de medida"
        verbose_name_plural = "Unidades de medidas"

    def __str__(self):
        return f"{self.capacidad} {self.unidad_medida}"
    
    def __unicode__(self):
        return f"{self.capacidad} {self.unidad_medida}"

    def clean(self):
        if self.capacidad and not str(self.capacidad).isdigit():
            raise ValidationError("El campo 'capacidad' debe ser un entero.")
        super().clean()
