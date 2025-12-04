import os
from django.core.validators import FileExtensionValidator
from django.db import models
from bases.bases.models import ModeloBase
from produccion.choices import CHOICE_ESTADO_PROD
from producto.models import Producto
from envase_embalaje.models import EnvaseEmbalaje
from nomencladores.almacen.models import Almacen


# Create your models here.

class Envasado(ModeloBase):
    estado = models.CharField(
        max_length=255,
        verbose_name="Estado",
        choices=CHOICE_ESTADO_PROD,
    )

    producto = models.ForeignKey(
        Producto, on_delete=models.DO_NOTHING,
        null=True, verbose_name="Producto a envasar"
    )

    cant_prod = models.IntegerField(
        null=False, blank=False,
        verbose_name="Cantidad del producto"
    )

    envases = models.ForeignKey(
        EnvaseEmbalaje, on_delete=models.DO_NOTHING,
        null=False, blank=False,
        verbose_name="Envase a utilizar"
    )

    cant_envases = models.IntegerField(
        null=False, blank=False,
        verbose_name="Cantidad de envases necesarios"
    )
    cant_envasados = models.IntegerField(
        null=False, blank=False,
        verbose_name="Cantidad de envases necesarios"
    )

    almacen_det = models.ForeignKey(
         Almacen, on_delete=models.DO_NOTHING,
        null=False, blank=False,
        verbose_name="Almacen destino"
    )
