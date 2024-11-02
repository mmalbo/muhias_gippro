from django.db import models

from bases.models import ModeloBase


class Nomenclador(ModeloBase):
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre",
        default=""
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.nombre


class NomencladorCodificado(Nomenclador):
    codigo = models.CharField(
        max_length=255,
    )

    class Meta:
        abstract = True


class NomencladorCodificadoDpa(Nomenclador):
    codigo_dpa = models.CharField(
        max_length=50,
        unique=True,
    )

    class Meta:
        abstract = True
