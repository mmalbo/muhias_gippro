from django.db import models

from nomencladores.nomencladores.models import Nomenclador
from materia_prima.tipo_materia_prima.choices import CHOICE_TIPO

class TipoMateriaPrima(Nomenclador):
    tipo = models.CharField(verbose_name='Tipo de materia prima',
                            max_length=50,
                            choices=CHOICE_TIPO,
                            blank=False,
                            # default='',
                            null=False)
    ingrediente_activo = models.IntegerField(
        default=0,
        # unique=True,
        # editable=False,
        verbose_name="Ingrediente activo",
        null=True,
    )
    tipo_fragancia = models.CharField(
        max_length=255,
        null=True,
        verbose_name="Tipo de fragancia",
        blank=True,
        default="No tiene fragancia"
        # unique=True,

    )
    tipo_sustancia = models.CharField(
        max_length=255,
        # unique=True,
        # editable=False,
        verbose_name="Tipo de sustancia",
        null=True,
        default="No tiene sustancia",
        blank=True
    )
    tipo_color = models.CharField(
        max_length=255,
        # unique=True,
        # editable=False,
        verbose_name="Tipo de color",
        default="No tiene color",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Tipo de materia prima"
        verbose_name_plural = "Tipos de materias primas"

    # def __str__(self):
    #     return self.tipo