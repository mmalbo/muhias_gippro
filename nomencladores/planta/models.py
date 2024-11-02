from django.db import models
from bases.bases.models import ModeloBase


class Planta(ModeloBase):
    nombre = models.CharField(
        max_length=255,
        unique=True,
        # editable=False,
        verbose_name="Nombre",
        null=False,
    )

    propio = models.BooleanField(
        default=False,
        verbose_name="Propio",
    )

    class Meta:
        verbose_name = "Planta"
        verbose_name_plural = "Plantas"

    def __str__(self):
        return self.nombre
