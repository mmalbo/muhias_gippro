from django.core.validators import FileExtensionValidator
from django.db import models
import os
from datetime import datetime
from bases.bases.models import ModeloBase
from nomencladores.planta.models import Planta
from produccion.choices import CHOICE_ESTADO
from inventario.models import Inv_Mat_Prima
from producto.models import Producto


def generate_unique_filename(instance, filename):
    now = datetime.now()
    date_part = now.strftime('%Y%m%d%H%M%S')
    name_part, extension = os.path.splitext(filename)
    return f'pruebas_quimicas/{name_part}_{date_part}{extension}'


class Produccion(ModeloBase):
    lote = models.CharField(unique=True, null=False, blank=False, max_length=20, verbose_name="Lote",)

    #nombre_producto = models.CharField(max_length=255, verbose_name="Nombre del producto", null=False,)
    catalogo_producto = models.ForeignKey(Producto, on_delete=models.PROTECT, verbose_name="Producto", null=True,
        related_name='producciones'
    )

    prod_result = models.BooleanField(default=False, verbose_name="Producto base",)

    cantidad_estimada = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0, 
                                            verbose_name="Cantidad estimada",)

    cantidad_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cantidad real",)

    pruebas_quimicas = models.FileField(upload_to=generate_unique_filename, null=True, blank=True, verbose_name="Pruebas químicas",
        validators=[FileExtensionValidator(allowed_extensions=['pdf','doc','docx','xls','xlsx','jpg','jpeg','png'])])
    
    prod_conform = models.BooleanField(null=True, blank=True, default=False, verbose_name="Producto Conforme",)

    costo = models.FloatField(null=False, blank=False, verbose_name="Costo",)

    planta = models.ForeignKey(Planta, on_delete=models.DO_NOTHING, null=False, verbose_name="Planta")

    estado = models.CharField(verbose_name='Estado', max_length=50, choices=CHOICE_ESTADO, blank=False, null=False )

    observaciones_cancelacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones de Cancelación/Detención"
    )
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lote {self.lote} - {self.catalogo_producto.nombre_comercial}"

    @property
    def total_materias_primas(self):
        return self.inventarios_prod.count()

    def puede_ser_cancelada(self):
        """Determina si la producción puede ser cancelada"""
        return self.estado in ['Planificada', 'En proceso']

    def nombre_archivo_pruebas(self):
        """Retorna el nombre del archivo sin la ruta"""
        if self.pruebas_quimicas:
            return os.path.basename(self.pruebas_quimicas.name)
        return None
    
    def extension_archivo(self):
        """Retorna la extensión del archivo"""
        if self.pruebas_quimicas:
            return os.path.splitext(self.pruebas_quimicas.name)[1].lower()
        return None

class Prod_Inv_MP(ModeloBase):
    lote_prod = models.ForeignKey(
        Produccion,  # Referencia al modelo completo
        on_delete=models.DO_NOTHING, verbose_name="Lote producto",
        related_name='inv_mp'
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
    