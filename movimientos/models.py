from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen, Responsable
from produccion.envasado.models import Envasado
from produccion.models import Produccion
from materia_prima.models import MateriaPrima

class Vale_Movimiento_Almacen(ModeloBase):
    consecutivo = models.IntegerField(null=False, verbose_name="Código del vale")
    # Revisar aquí hay una inconsistencia, si se borra el almacén esteatributo dice que no hace nada, pero no puede ser nulo.
    almacen = models.ForeignKey(Almacen, on_delete=models.DO_NOTHING, verbose_name="Almacen_origen", null=False, blank=False,)
    fecha_movimiento = models.DateField(auto_now=True, null=False,verbose_name="Fecha de solicitud")

    def __str__(self):
        return f'Vale No. {self.consecutivo}. Fecha: {self.fecha_movimiento}'
    
    def save(self, *args, **kwargs):
        count = Vale_Movimiento_Almacen.objects.all().count()
        self.consecutivo = count +1
        super(Vale_Movimiento_Almacen, self).save(*args, **kwargs)

        
""" class Vale_Recepcion_Almacen(Vale_Movimiento_Almacen):
    fecha_solicitud = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )

    solicitud_produccion = models.ForeignKey(
        Produccion, on_delete=models.DO_NOTHING,
        null=True, blank=True,
        verbose_name="Producción"
    ) """

class Vale_Salida_Almacen_Produccion(Vale_Movimiento_Almacen):
    fecha_solicitud = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )

    solicitud_produccion = models.ForeignKey(
        Produccion, on_delete=models.DO_NOTHING,
        null=True, blank=True,
        verbose_name="Producción"
    )

class Vale_Salida_Almacen_Envasado(Vale_Movimiento_Almacen):
    fecha_solicitud = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )

    solicitud_envasado = models.ForeignKey(
        Envasado, on_delete=models.DO_NOTHING,
        null=True,
        verbose_name="Envasado"
    )


class Conduce(Vale_Movimiento_Almacen):
    fecha_solicitud = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )
        
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

class Movimiento_MP(ModeloBase):
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT,
        verbose_name="Materia prima",
        null=False, blank=False,
    )
    entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")
    vale = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=False, blank=False, related_name="movimientos")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")

    def __str__(self):
        entrada = 'Entrada ' if self.entrada else 'Salida '
        return f'{entrada} de {self.materia_prima.nombre} en {self.vale.almacen.nombre}'