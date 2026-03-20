from django.db import models

from bases.bases.models import ModeloBase


class TipoEnvaseEmbalaje(ModeloBase):

    codigo = models.CharField(max_length=255, verbose_name="Código")
    nombre = models.CharField(max_length=255, verbose_name="Nombre",blank=False, null=False, default="Tipo")

    def __str__(self):
        return self.nombre  # O cualquier campo que desees mostrar
