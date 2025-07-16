from django.db import models
from django.core.exceptions import ValidationError
from bases.bases.models import ModeloBase
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
import os

def factura_upload_to(instance, filename):
    # Obtenemos el tipo de adquisición
    if isinstance(instance, MateriaPrimaAdquisicion):
        folder_name = 'materia_prima'
    #elif isinstance(instance, EnvaseAdquisicion):
    #    folder_name = 'envase'
    #elif isinstance(instance, InsumosAdquisicion):
    #    folder_name = 'insumos' """
    else:
        raise ValidationError("Tipo de adquisición no válido")

    # Retornamos la ruta completa donde se guardará el archivo
    return os.path.join('facturas', folder_name, filename)

class Adquisicion(ModeloBase):
    fecha_compra = models.DateField(
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
        verbose_name="Cantidad elementos",
        null=False, default=1
    )

    #class Meta:
    #    abstract = True  # Define esta clase como abstracta

#Cambiando al modelado inicial de muchos a muchos explicito porque en una adquisición se 
#se pueden adquirir varias materias primas.
class MateriaPrimaAdquisicion(ModeloBase):
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT,  # Cambiado a PROTECT
                                      verbose_name="Materia prima"
    )
    adquisicion = models.ForeignKey(Adquisicion, on_delete=models.PROTECT, 
                                    verbose_name="Adquisición")
    cantidad = models.IntegerField(default=1, verbose_name="Cantidad de la materia prima")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['materia_prima', 'adquisicion'],
                name='matp_adquis'
            )
        ]
    def __str__(self):
        return f"{self.materia_prima} - {self.adquisicion} - Cantidad: {self.cantidad}"


""" class EnvaseAdquisicion(Adquisicion):
    envase = models.ForeignKey(
        EnvaseEmbalaje, on_delete=models.PROTECT,  # Cambiado a PROTECT
        verbose_name="Envase o embalaje"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['envase', 'fecha_compra', 'factura'],
                name='unique_envase_adquisicion'
            )
        ]


class InsumosAdquisicion(Adquisicion):
    insumo = models.ForeignKey(
        InsumosOtros, on_delete=models.PROTECT,  # Cambiado a PROTECT
        verbose_name="Insumo adquirido"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['insumo', 'fecha_compra', 'factura'],
                name='unique_insumos_adquisicion'
            )
        ] """