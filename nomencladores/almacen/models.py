from django.db import models
from bases.bases.models import ModeloBase
from usuario.models import CustomUser
from .choices import Conceptos, obtener_conceptos_almacen

class Almacen(ModeloBase):
    nombre = models.CharField( max_length=255, unique=True, verbose_name="Nombre", null=False, )
    ubicacion = models.CharField( max_length=255, verbose_name="Ubicación", null=False, )
    propio = models.BooleanField( default=False, verbose_name="Propio", )
    concepto = models.CharField( max_length=20, choices=obtener_conceptos_almacen(), default='inventario', 
                                verbose_name='Concepto de almacen')
    responsable = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, verbose_name="Responsable de almacén", 
                                    null=True, blank=True)

    class Meta:
        verbose_name = "Almacen"
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre
