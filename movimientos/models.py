from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen
from produccion.envasado.models import Envasado
from produccion.models import Produccion
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros as Insu
from usuario.models import CustomUser

class Transportista(ModeloBase):
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

# Esta es la clase que registra los movimientos de almacén y guarda todos los datos para generar el vale correspondiente
class Vale_Movimiento_Almacen(ModeloBase):
    consecutivo = models.IntegerField(null=False, verbose_name="Código del vale")
    # Revisar aquí hay una inconsistencia, si se borra el almacén esteatributo dice que no hace nada, pero no puede ser nulo.
    almacen = models.ForeignKey(Almacen, on_delete=models.DO_NOTHING, verbose_name="Almacen_origen", null=False, blank=False,)
    fecha_movimiento = models.DateField(auto_now=True, null=False,verbose_name="Fecha de solicitud")
    suministrador = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.DO_NOTHING, verbose_name="Suministrador")
    orden_No = models.IntegerField(blank=True, null=True, verbose_name="Número de orden")
    lote_No = models.IntegerField(blank=True, null=True, verbose_name="Número de lote")
    transportista = models.ForeignKey(Transportista, blank=True, null=True, on_delete=models.DO_NOTHING, verbose_name="Transportista")
    chapa = models.CharField(blank=True, null=True, max_length=150, verbose_name="Chapa del vehículo")
    despachado_por = models.CharField(blank=True, null=True, max_length=150, verbose_name="Almacenero que despacha")
    recibido_por = models.CharField(blank=True, null=True, max_length=150, verbose_name="Quien recibe")
    autorizado_por = models.CharField(blank=True, null=True, max_length=150, verbose_name="Autoriza")
    entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")

    def __str__(self):
        return f'Vale No. {self.consecutivo}. Fecha: {self.fecha_movimiento}'
    
    def save(self, *args, **kwargs):
        count = Vale_Movimiento_Almacen.objects.all().count()
        self.consecutivo = count +1
        super(Vale_Movimiento_Almacen, self).save(*args, **kwargs)
        
#Relación mucho a mucho de movimiento con Produccion
class Vale_Salida_Almacen_Produccion(ModeloBase):
    fecha_solicitud = models.DateField(
        auto_now=True, null=False,
        verbose_name="Fecha de solicitud"
    )

    solicitud_produccion = models.ForeignKey(
        Produccion, on_delete=models.DO_NOTHING,
        null=True, blank=True,
        verbose_name="Producción"
    )

    vale_movimiento = models.ForeignKey(
        Vale_Movimiento_Almacen, on_delete=models.DO_NOTHING,
        null=True, blank=True,
        verbose_name="Movimiento"
    )


class Vale_Salida_Almacen_Envasado(ModeloBase):
    fecha_solicitud = models.DateField(
        auto_now=True, null=True,
        verbose_name="Fecha de solicitud"
    )

    solicitud_envasado = models.ForeignKey(
        Envasado, on_delete=models.DO_NOTHING,
        null=True,
        verbose_name="Envasado"
    )

    vale_movimiento = models.ForeignKey(
        Vale_Movimiento_Almacen, on_delete=models.DO_NOTHING,
        null=True, blank=True,
        verbose_name="Movimiento"
    )

#Relación mucho a mucho de vale con materia prima 
class Movimiento_MP(ModeloBase):
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT,
        verbose_name="Materia prima",
        null=True
    )
    vale = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=False, blank=False, related_name="movimientos")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")
    #entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")

    def __str__(self):
        entrada = 'Entrada ' if self.vale.entrada else 'Salida '
        return f'{entrada} de {self.materia_prima.nombre} en {self.vale.almacen.nombre}'

#Relación mucho a mucho de vale con envase y embalaje 
class Movimiento_EE(ModeloBase):
    envase_embalaje = models.ForeignKey(EnvaseEmbalaje, on_delete=models.PROTECT,
        verbose_name="Envase o embalaje",
        null=False, blank=False,
    )
    vale_e = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=False, blank=False, related_name="movimientos_e")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")    

    def __str__(self):
        entrada = 'Entrada ' if self.vale_e.entrada else 'Salida '
        return f'{entrada} de {self.envase_embalaje.codigo_envase} en {self.vale_e.almacen.nombre}'

#Relación mucho a mucho de vale con materia prima     
class Movimiento_Ins(ModeloBase):
    insumo = models.ForeignKey(Insu, on_delete=models.PROTECT,
        verbose_name="Insumos",
        null=False, blank=False,
    )
    vale_e = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=False, blank=False, related_name="movimientos_i")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")

    def __str__(self):
        entrada = 'Entrada ' if self.vale_e.entrada else 'Salida '
        return f'{entrada} de {self.insumo.nombre} en {self.vale_e.almacen.nombre}'
    
