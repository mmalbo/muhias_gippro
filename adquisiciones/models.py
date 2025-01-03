from django.db import models
from bases.bases.models import ModeloBase
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
import os


def factura_upload_to(instance, filename):
    # Obtenemos el tipo de adquisicion
    if isinstance(instance, MateriaPrimaAdquisicion):
        folder_name = 'materia_prima'
    elif isinstance(instance, EnvaseAdquisicion):
        folder_name = 'envase'
    elif isinstance(instance, InsumosAdquisicion):
        folder_name = 'insumos'
    else:
        folder_name = 'otros'

    # Retornamos la ruta completa donde se guardará el archivo
    return os.path.join('facturas', folder_name, filename)


class Adquisicion(ModeloBase):
    fecha_compra = models.DateTimeField(
        verbose_name="Fecha de la compra",
        null=True,
        editable=True
    )
    factura = models.FileField(
        verbose_name="Factura",
        null=True, blank=True,
        upload_to=factura_upload_to  # Usamos la función definida
    )
    importada = models.BooleanField(
        verbose_name="Importada",
        null=False, default=False
    )
    cantidad = models.IntegerField(
        verbose_name="Cantidad",
        null=False, default=1
    )

    class Meta:
        abstract = True  # Define esta clase como abstracta


class MateriaPrimaAdquisicion(Adquisicion):
    materia_prima = models.ForeignKey(
        MateriaPrima, on_delete=models.DO_NOTHING,
        verbose_name="Materia prima adquirida"
    )

    class Meta:
        unique_together = (('materia_prima', 'fecha_compra', 'factura'),)


class EnvaseAdquisicion(Adquisicion):
    envase = models.ForeignKey(
        EnvaseEmbalaje, on_delete=models.DO_NOTHING,
        verbose_name="Envase o embalaje"
    )

    class Meta:
        unique_together = (('envase', 'fecha_compra', 'factura'),)


class InsumosAdquisicion(Adquisicion):
    insumo = models.ForeignKey(
        InsumosOtros, on_delete=models.DO_NOTHING,
        verbose_name="Insumo adquirido"
    )

    class Meta:
        unique_together = (('insumo', 'fecha_compra', 'factura'),)
