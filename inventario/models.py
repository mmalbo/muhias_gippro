from django.db import models

# Create your models here.
from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen
from materia_prima.models import MateriaPrima
from producto.models import Producto
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros

class Inv_Mat_Prima(ModeloBase):
    materia_prima = models.ForeignKey(
        MateriaPrima, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Materia prima", related_name='inventarios_mp'
    )
    almacen = models.ForeignKey(
        Almacen, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Almacen", related_name='inventarios_mp'
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=0)

    def __str__(self):
        return f'{self.materia_prima.nombre} en {self.almacen.nombre}'

class Inv_Producto(ModeloBase):
    producto = models.ForeignKey(
        Producto, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Producto", related_name='inventarios_prod'
    )
    almacen = models.ForeignKey(
        Almacen, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Almacen", related_name='inventarios_prod'
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=0)

    def __str__(self):
        return f'{self.producto.nombre_comercial} en {self.almacen.nombre}'
     
class Inv_Envase(ModeloBase):
    envase = models.ForeignKey(
        EnvaseEmbalaje, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Envase o embalaje", related_name='inventarios_env'
    )
    almacen = models.ForeignKey(
        Almacen, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Almacen", related_name='inventarios_env'
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=0)

    def __str__(self):
        return f'{self.envase.codigo_envase} en {self.almacen.nombre}'

class Inv_Insumos(ModeloBase):
    insumos = models.ForeignKey(
        InsumosOtros, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Insumos", related_name='inventarios_ins'
    )
    almacen = models.ForeignKey(
        Almacen, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Almacen", related_name='inventarios_ins'
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=0)

    def __str__(self):
        return f'{self.insumos.nombre} en {self.almacen.nombre}'