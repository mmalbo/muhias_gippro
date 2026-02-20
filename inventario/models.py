import uuid
from django.db import models

# Create your models here.
from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen
from materia_prima.models import MateriaPrima
from producto.models import Producto
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros

# models.py - Agregar esta clase al inicio
class ItemInventarioBase(ModeloBase):
    """Clase abstracta base para todos los tipos de inventario"""
    almacen = models.ForeignKey(
        Almacen, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Almacén"
    )
    cantidad = models.DecimalField(
        max_digits=7, decimal_places=2, 
        verbose_name="Cantidad", null=False, default=0
    )
    
    # Campos para identificar el tipo de item
    tipo = models.CharField(max_length=20, default='', editable=False)
    item_id = models.UUIDField(default=uuid.uuid4)
    #descripcion = models.CharField(max_length=150, default='')
    
    class Meta:
        abstract = True
    
    def get_item(self):
        """Método para obtener el item específico según el tipo"""
        if self.tipo == 'materia_prima':
            return self.inventarios_mp.first()
        elif self.tipo == 'producto':
            return self.inventarios_prod.first()
        elif self.tipo == 'envase':
            return self.inventarios_env.first()
        elif self.tipo == 'insumo':
            return self.inventarios_ins.first()
        return None

# Modificar las clases existentes para heredar de ItemInventarioBase
class Inv_Mat_Prima(ItemInventarioBase):
    materia_prima = models.ForeignKey(
        MateriaPrima, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Materia prima", related_name='inventarios_mp'
    )
    
    def save(self, *args, **kwargs):
        self.tipo = 'materia_prima'
        self.item_id = self.materia_prima.id
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.materia_prima.nombre} en {self.almacen.nombre}'

class Inv_Producto(ItemInventarioBase):
    lote = models.CharField(
        null=True, blank=True, max_length=20, 
        verbose_name="Lote"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Producto", related_name='inventarios_prod'
    )
    
    def save(self, *args, **kwargs):
        self.tipo = 'producto'
        self.item_id = self.producto.id
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.producto.nombre_comercial} en {self.almacen.nombre}'
 
class Inv_Envase(ItemInventarioBase):
    envase = models.ForeignKey(
        EnvaseEmbalaje, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Envase o embalaje", related_name='inventarios_env'
    )

    def save(self, *args, **kwargs):
        self.tipo = 'envase'
        self.item_id = self.envase.id
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.envase.codigo_envase} en {self.almacen.nombre}'

class Inv_Insumos(ItemInventarioBase):
    insumos = models.ForeignKey(
        InsumosOtros, on_delete=models.DO_NOTHING,
        null=False,
        verbose_name="Insumos", related_name='inventarios_ins'
    )

    def save(self, *args, **kwargs):
        self.tipo = 'insumo'
        self.item_id = self.insumos.id
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.insumos.nombre} en {self.almacen.nombre}'