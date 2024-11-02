from django.db import models
from bases.bases.models import ModeloBase


class HojaSeguridad(ModeloBase):
    nombre_sustancia_quimica = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Nombre de la sustancia química",
        null=True,
        blank=True,
    )
    sinonimo = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Sinónimo",
        null=False,
    )
    uso_recomendado = models.TextField(
      # editable=False,
        verbose_name="Sinónimo",
        null=False,
    )
    telefono_emergencia = models.IntegerField(
      # editable=False,
        verbose_name="Teléfono de emergencia",
        null=False,
    )

    clasificacion_sustancia_peligrosa = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Clasificación de sustancia peligrosa",
        null=True,
        blank=True,
    )

    column = models.IntegerField(
      # editable=False,
        verbose_name="Column",
        null=False,
    )
