from django.db import models
from bases.bases.models import ModeloBase


class Almacen(ModeloBase):
    nombre = models.CharField(
        max_length=255,
        unique=True,
        # editable=False,
        verbose_name="Nombre",
        null=False,
    )
    ubicacion = models.CharField(
        max_length=255,
        verbose_name="Ubicación",
        null=False,
    )
    propio = models.BooleanField(
        default=False,
        verbose_name="Propio",
    )

    class Meta:
        verbose_name = "Almacen"
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre


class Responsable(ModeloBase):
    responsable_CI = models.CharField(
        max_length=11,
        verbose_name="Carnet de identidad",
        null=True, blank=True,
    )

    responsable_Nombre = models.CharField(
        max_length=200, null=True,
        verbose_name='Nombre y apellidos',
    )

    responsable_Cargo = models.CharField(
        max_length=200, null=False,
        verbose_name="Responsabilidad(cargo)"
    )


#
# from produccion.envasado.models import Envasado
# from produccion.models import Produccion
#
#
# class Vale_Salida_Almacen(ModeloBase):
#     consecutivo = models.IntegerField(
#         null=False,
#         verbose_name="Código del vale"
#     )
#
#     almacen_origen = models.ForeignKey(
#         Almacen, on_delete=models.DO_NOTHING,
#         verbose_name="Almacen_origen",
#         null=False, blank=False,
#     )
#
#     fecha_solicitud = models.DateField(
#         auto_now=True, null=False,
#         verbose_name="Fecha de solicitud"
#     )
#
#     fecha_movimiento = models.DateField(
#         auto_now=True, null=False,
#         verbose_name="Fecha de solicitud"
#     )
#
#     solicitud_produccion = models.ForeignKey(
#         Produccion, on_delete=models.DO_NOTHING,
#         null=True, blank=True,
#         verbose_name="Producción"
#     )
#
#     solicitud_envasado = models.ForeignKey(
#         Envasado, on_delete=models.DO_NOTHING,
#         null=True,
#         verbose_name="Envasado"
#     )
#
#
# class Conduce(Vale_Salida_Almacen):
#     chapa_vehiculo = models.CharField(
#         max_length=10, null=False,
#         blank=True,
#         verbose_name="Chapa"
#     )
#
#     responsable = models.ForeignKey(
#         Responsable, on_delete=models.DO_NOTHING,
#         null=True,
#         verbose_name="Responsable del movimiento"
#     )