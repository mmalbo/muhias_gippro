from django.core.validators import FileExtensionValidator
from django.db import models
import os
from datetime import datetime
from bases.bases.models import ModeloBase
from nomencladores.planta.models import Planta
from produccion.choices import CHOICE_ESTADO
from inventario.models import Inv_Mat_Prima


def generate_unique_filename(instance, filename):
    now = datetime.now()
    date_part = now.strftime('%Y%m%d%H%M%S')
    name_part, extension = os.path.splitext(filename)
    return f'pruebas_quimicas/{name_part}_{date_part}{extension}'


class Produccion(ModeloBase):
    lote = models.CharField(unique=True, null=False, blank=False, max_length=20, verbose_name="Lote",)

    nombre_producto = models.CharField(max_length=255, verbose_name="Nombre del producto", null=False,)

    prod_result = models.BooleanField(default=False, verbose_name="Producto base",)

    cantidad_estimada = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, 
                                            verbose_name="Cantidad estimada",)

    cantidad_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cantidad real",)

    pruebas_quimicas = models.FileField(upload_to=generate_unique_filename, null=True, blank=True, verbose_name="Pruebas químicas",
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    costo = models.FloatField(null=False, blank=False, verbose_name="Costo",)

    planta = models.ForeignKey(Planta, on_delete=models.DO_NOTHING, null=False, verbose_name="Planta")

    estado = models.CharField(verbose_name='Estado', max_length=50, choices=CHOICE_ESTADO, blank=False, null=False )

    def __str__(self):
        return f"Lote {self.lote} - {self.nombre_producto}"

    @property
    def total_materias_primas(self):
        return self.prod_inv_mp.count()

class Prod_Inv_MP(ModeloBase):
    lote_prod = models.ForeignKey(
        Produccion,  # Referencia al modelo completo
        on_delete=models.DO_NOTHING, verbose_name="Lote producto",
    )

    inv_materia_prima = models.ForeignKey(
        Inv_Mat_Prima,  # Referencia al modelo completo
        on_delete=models.DO_NOTHING,
        verbose_name="Materia prima",
    )

    cantidad_materia_prima = models.IntegerField(
        null=False,
        blank=False,
        default=1,
        verbose_name="Cantidad de la materia prima",
    )
    