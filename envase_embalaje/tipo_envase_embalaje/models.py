from django.db import models

from bases.bases.models import ModeloBase


class TipoEnvaseEmbalaje(ModeloBase):
    # nombre = models.CharField(
    #     max_length=255,
    #     blank=False, null=False,
    #     verbose_name="Nombre"
    # )
    codigo = models.CharField(

        max_length=255,
        verbose_name="Código"
    )

    def __str__(self):
        return self.codigo  # O cualquier campo que desees mostrar
