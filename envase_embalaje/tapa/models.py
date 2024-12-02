from django.db import models
from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje

class Tapa(TipoEnvaseEmbalaje):
    nombre = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name="Nombre"
    )
    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        null=True,  # Puedes considerar cambiar a False si el color es obligatorio
        verbose_name="Color"
    )
    descripcion = models.TextField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    class Meta:
        verbose_name = "Tapa"
        verbose_name_plural = "Tapas"
        ordering = ['nombre']  # Ordenar por nombre por defecto

    def __str__(self):
        return self.nombre