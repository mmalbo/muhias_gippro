from django.db import models
from bases.bases.models import ModeloBase


class Adquisicion(ModeloBase):
    fecha_compra = models.DateTimeField(
        verbose_name="Fecha de la compra",
        null=False, blank=False
    )
    factura = models.FileField(
        verbose_name="Factura",
        null=False, blank=False
    )
    importada = models.BooleanField(
        verbose_name="Importada",
        null=False, default=False
    )


from materia_prima.models import MateriaPrima  # Importación local


class MateriaPrimaAdquisicion(ModeloBase):
    adquisicion_id = models.ForeignKey(
        Adquisicion, on_delete=models.DO_NOTHING,

        verbose_name="Adquisición de la materia prima"
    )
    materia_prima_id = models.ForeignKey(
        MateriaPrima, on_delete=models.DO_NOTHING,
        verbose_name="Materia prima adquirida")

    cantidad = models.IntegerField(
        verbose_name="Cantidad",
        null=False, default=1
    )


from envase_embalaje.models import EnvaseEmbalaje  # Importación local


class EnvaseAdquisicion(ModeloBase):
    adquisicion_id = models.ForeignKey(
        Adquisicion, on_delete=models.DO_NOTHING,

        verbose_name="Adquisición de envase"
    )
    envase_id = models.ForeignKey(
        EnvaseEmbalaje, on_delete=models.DO_NOTHING,
        verbose_name="Envase o embalaje"
    )

    cantidad = models.IntegerField(
        verbose_name="Cantidad",
        null=False, default=1
    )


from InsumosOtros.models import InsumosOtros


class InsumosAdquisicion(ModeloBase):
    adquisicion_id = models.ForeignKey(
        Adquisicion, on_delete=models.DO_NOTHING,

        verbose_name="Adquisición de insumos"
    )
    envase_id = models.ForeignKey(
        InsumosOtros, on_delete=models.DO_NOTHING,
        verbose_name="Insumo adquirido"
    )

    cantidad = models.IntegerField(
        verbose_name="Cantidad",
        null=False, default=1
    )
