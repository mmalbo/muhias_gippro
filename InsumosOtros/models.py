from django.db import models
from bases.bases.models import ModeloBase

from nomencladores.almacen.models import Almacen


# Create your models here.

class InsumosOtros(ModeloBase):
    codigo = models.CharField(
        verbose_name="Código de insumo",
        unique=True,
        null=False, max_length=20
    )

    ESTADOS = [
        ('comprado', 'Comprado'),
        ('en_almacen', 'En almacén'),
        ('reservado', 'Reservado'),
    ]
    estado = models.CharField(
        choices=ESTADOS,
        max_length=255,
        null=False,
        verbose_name='Estado'
    )

    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre",
        null=False, blank=False,
    )

    descripcion = models.CharField(
        max_length=600,
        verbose_name="Descripción",
        null=False, blank=False,
    )

    cantidad_almacen = models.IntegerField(
        null=True, blank=False,
        default=0,
        verbose_name="Cantidad",
    )

    costo = models.FloatField(
        null=True,
        blank=False,
        default=0,
        verbose_name="Costo",
    )

    """ almacen = models.ForeignKey(
        Almacen, on_delete=models.SET_NULL,
        null=True,
        verbose_name='Almacen ubicación'
    ) """
    def __str__(self):
        return self.nombre
