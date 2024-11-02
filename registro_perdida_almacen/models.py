from django.db import models
from bases.bases.models import ModeloBase
from materia_prima.models import MateriaPrima
# from almacen.models import Almacen


class MateriaPrimaAlmacen(ModeloBase):
    cantidad = models.IntegerField(
        verbose_name='Cantidad',
      # editable=False,
        null=True,
        blank=True,
    )
    causa = models.TextField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Nombre",
        null=True,
        blank=True,
    )
    fecha = models.DateField(
        verbose_name='Fecha',
      # editable=False,

    )
