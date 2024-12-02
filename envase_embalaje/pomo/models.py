from django.db import models
from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje

class Pomo(TipoEnvaseEmbalaje):
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre"
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.DO_NOTHING,
        verbose_name="Color"
    )
    forma = models.CharField(
        max_length=255,
        verbose_name="Forma"
    )
    material = models.CharField(
        max_length=255,
        verbose_name="Material"
    )

    class Meta:
        verbose_name = "Pomo"
        verbose_name_plural = "Pomos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre