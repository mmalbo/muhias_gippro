from django.db import models

from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje


class Pomo(TipoEnvaseEmbalaje):
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
    forma = models.TextField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Forma"
    )
    material = models.TextField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Material"
    )
