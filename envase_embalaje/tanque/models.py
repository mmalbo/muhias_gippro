from django.db import models

from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje


class Tanque(TipoEnvaseEmbalaje):
    nombre = models.CharField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Nombre"
    )
    color = models.ForeignKey(
        Color, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Color"
    )
    material = models.CharField(
        max_length=255, null=False,
        blank=False, 
        verbose_name="Material"
    )

