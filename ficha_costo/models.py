from django.db import models
from bases.bases.models import ModeloBase


class FichaCosto(ModeloBase):
    costo_unit_prom = models.FloatField(
        # editable=False,
        verbose_name="Costo unitario promocional",
        null=True,
        default=0,
        blank=True,
    )
    costo_maximo = models.FloatField(
        null=True,
        default=0,
        blank=True,
        # editable=False,
        verbose_name="Costo máximo",
    )
