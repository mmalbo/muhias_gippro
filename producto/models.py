from django.db import models

from bases.bases.models import ModeloBase
from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen


class Producto(ModeloBase):
    codigo_producto = models.CharField(
        null=True,
        blank=True,
        max_length=20,
        verbose_name="Código del producto",
    )

    nombre_comercial = models.CharField(
        max_length=255,
        verbose_name="Nombre comercial",
        null=False,
    )

    product_final = models.BooleanField(
        null=False, blank=False,
        default=True,
        verbose_name="Producto final"
    )

    cantidad_alm = models.IntegerField(
        null=False,
        blank=False,
        default=0,
        verbose_name="Cantidad almacenada",
    )

    ficha_tecnica_folio = models.OneToOneField(
        FichaTecnica, on_delete=models.CASCADE,
        null=True,
        verbose_name="Ficha técnica folio"
    )
    ficha_costo = models.FileField(
        null=True,
        verbose_name="Ficha de costo"
    )

    almacen=models.ForeignKey(
        Almacen, on_delete=models.CASCADE,
        verbose_name="Almacen",
        null=False,
    )