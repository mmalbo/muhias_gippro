from django.db import models
from django.apps import apps
from bases.bases.models import ModeloBase
from .formato.models import Formato
from .tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from nomencladores.almacen.models import Almacen


class EnvaseEmbalaje(ModeloBase):
    codigo_envase = models.CharField(
        unique=True, null=False,
        blank=False, max_length=20,
        verbose_name="Código del envase",
    )

    tipo_envase_embalaje = models.ForeignKey(
        TipoEnvaseEmbalaje, on_delete=models.DO_NOTHING,
        null=True,
        verbose_name="Tipo de envase de embalaje"
    )

    formato = models.ForeignKey(
        Formato, on_delete=models.DO_NOTHING,
        null=True,
        verbose_name="Formato de envase"
    )

    ESTADOS = [
        ('comprado', 'Comprado'),
        ('en_almacen', 'En almacén'),
        ('reservado', 'Reservado'),
    ]
    estado = models.CharField(
        choices=ESTADOS,
        max_length=255,
        blank=False, null=False,
        verbose_name='Estado'
    )

    cantidad = models.IntegerField(
        null=True,
        default=0,
        verbose_name="Cantidad en almacen",
    )

    almacen = models.ForeignKey(
        Almacen, on_delete=models.SET_NULL,
        null=True,
        verbose_name='Almacen'
    )

    class Meta:
        verbose_name = "Envase o embalaje"
        verbose_name_plural = "Envases o embalajes"

    def __str__(self):
        return self.tipo_envase_embalaje.codigo

    @property
    def all_almacenes(self):
        Almacen = apps.get_model('almacen', 'Almacen')
        return Almacen.objects.filter(envases=self)
