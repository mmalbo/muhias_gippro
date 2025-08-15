from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen, Responsable
from produccion.envasado.models import Envasado
from produccion.models import Produccion


class Vale_Salida_Almacen(ModeloBase):
    consecutivo = models.IntegerField(
        null=False,
        verbose_name="Código del vale"
    )

    almacen_origen = models.ForeignKey(
        Almacen, on_delete=models.DO_NOTHING,
        verbose_name="Almacen_origen",
        null=False, blank=False,
    )

    fecha_solicitud = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )

    fecha_movimiento = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )

    solicitud_produccion = models.ForeignKey(
        Produccion, on_delete=models.DO_NOTHING,
        null=True, blank=True,
        verbose_name="Producción"
    )

    solicitud_envasado = models.ForeignKey(
        Envasado, on_delete=models.DO_NOTHING,
        null=True,
        verbose_name="Envasado"
    )


class Conduce(Vale_Salida_Almacen):
    chapa_vehiculo = models.CharField(
        max_length=10, null=False,
        blank=True,
        verbose_name="Chapa"
    )

    responsable = models.ForeignKey(
        Responsable, on_delete=models.DO_NOTHING,
        null=True,
        verbose_name="Responsable del movimiento"
    )
