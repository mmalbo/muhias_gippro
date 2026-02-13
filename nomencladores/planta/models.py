from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen

class Planta(ModeloBase):
    nombre = models.CharField(
        max_length=255,
        unique=True,
        # editable=False,
        verbose_name="Nombre",
        null=False,
    )

    propio = models.BooleanField(
        default=False,
        verbose_name="Propia",
    )

    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, 
                               related_name='planta_asociada', 
                               null=True, blank=True,
                               verbose_name="Almacén asociado a la planta")

    class Meta:
        verbose_name = "Planta"
        verbose_name_plural = "Plantas"

    def __str__(self):
        return self.nombre
