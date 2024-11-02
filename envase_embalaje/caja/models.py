from django.db import models
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje


class Caja(TipoEnvaseEmbalaje):
    nombre = models.CharField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Nombre"
    )
    tamanno = models.TextField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Tamaño"
    )
    material = models.TextField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Material"
    )
