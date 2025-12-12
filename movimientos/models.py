from django.db import models
from bases.bases.models import ModeloBase
from nomencladores.almacen.models import Almacen
from produccion.envasado.models import Envasado
from materia_prima.models import MateriaPrima
from producto.models import Producto
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros as Insu
from usuario.models import CustomUser

class Transportista(ModeloBase):
    cI = models.CharField(
        max_length=11,
        verbose_name="Carnet de identidad",
        null=True, blank=True,
    )

    nombre = models.CharField(
        max_length=200, null=True,
        verbose_name='Nombre y apellidos',
    )

    cargo = models.CharField(
        max_length=200, null=False,
        verbose_name="Responsabilidad(cargo)"
    )

# Esta es la clase que registra los movimientos de almacén y guarda todos los datos para generar el vale correspondiente
class Vale_Movimiento_Almacen(ModeloBase):
    
    VALE_TYPES = (('Entrega','Entrega'),
                      ('Transferencia','Transferencia'),
                      ('Ajuste de inventario','Ajuste de inventario'),
                      ('Recepción','Recepción'),
                      ('Vale de devolución','Vale de devolución'),
                      ('Solicitud','Solicitud'),
                      ('Producción terminada','Producción terminada'),
                      ('Conduce','Conduce'),
    )
    tipo = models.CharField(choices=VALE_TYPES, max_length=25, default='Recepción', verbose_name = "Tipo de movimiento")
    consecutivo = models.IntegerField(null=False, verbose_name="Código del vale")
    # Revisar aquí hay una inconsistencia, si se borra el almacén esteatributo dice que no hace nada, pero no puede ser nulo.
    almacen = models.ForeignKey(Almacen, on_delete=models.DO_NOTHING, verbose_name="Almacen que registra", null=True, blank=False,)
    fecha_movimiento = models.DateField(auto_now=True, null=False,verbose_name="Fecha de solicitud")
    suministrador = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.DO_NOTHING, verbose_name="Suministrador")
    orden_No = models.IntegerField(blank=True, null=True, verbose_name="Número de orden")
    lote_No = models.IntegerField(blank=True, null=True, verbose_name="Número de lote")
    transportista = models.CharField(blank=True, null=True, default='', max_length=150, verbose_name="Transportista")
    transportista_cI = models.CharField(blank=True, null=True, default='', max_length=11, verbose_name="Carnet de identidad")
    origen = models.CharField(blank=True, null=True, max_length=150, verbose_name="Origen del movimiento")
    destino = models.CharField(blank=True, null=True, max_length=150, verbose_name="Destino del  movimiento")
    chapa = models.CharField(blank=True, null=True, max_length=150, verbose_name="Chapa del vehículo")
    despachado_por = models.CharField(blank=True, null=True, max_length=150, verbose_name="Almacenero que despacha")
    recibido_por = models.CharField(blank=True, null=True, max_length=150, verbose_name="Quien recibe")
    autorizado_por = models.CharField(blank=True, null=True, max_length=150, verbose_name="Autoriza")
    descripcion = models.CharField(blank=True, null=True, max_length=250, verbose_name="Descripción del movimiento")
    entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")
    despachado = models.BooleanField(default=False, verbose_name="Verdadero: Cuando se haga efectivo el movimiento")

    def __str__(self):
        return f'Vale No. {self.consecutivo}. Fecha: {self.fecha_movimiento}'
    
    def save(self, *args, **kwargs):
        count = Vale_Movimiento_Almacen.objects.all().count()
        self.consecutivo = count +1
        super(Vale_Movimiento_Almacen, self).save(*args, **kwargs)

    @property
    def tipo_inventario(self):
        from produccion.models import Prod_Inv_MP
        print('tipo inventario')
        if Movimiento_MP.objects.filter(vale=self).exists():
            print('Materias primas')
            return 'Materias primas'
        if Movimiento_EE.objects.filter(vale_e=self).exists():
            return 'Envases y embalajes'
        if Movimiento_Ins.objects.filter(vale_e=self).exists():
            return 'Insumos'
        if Movimiento_Prod.objects.filter(vale_e=self).exists():
            return 'Productos'
        if Vale_Salida_Almacen_Produccion.objects.filter(vale_movimiento=self).exists():
            return 'Salida a producción'
        if Vale_Salida_Almacen_Envasado.objects.filter(vale_movimiento= self).exists():
            return 'Salida a envasado'
        if Prod_Inv_MP.objects.filter(vale=self).exists():
            print('Solicitud de produccion')
            return 'Solicitud desde producción'
        print("No encontre nada")

    @property
    def cant_elementos(self):
        from produccion.models import Prod_Inv_MP
        print("cantidad de elementos")
        if Movimiento_MP.objects.filter(vale=self).exists():
            return Movimiento_MP.objects.filter(vale=self).count()
        if Movimiento_EE.objects.filter(vale_e=self).exists():
            return Movimiento_EE.objects.filter(vale_e=self).count()
        if Movimiento_Ins.objects.filter(vale_e=self).exists():
            return Movimiento_Ins.objects.filter(vale_e=self).count()
        if Movimiento_Prod.objects.filter(vale_e=self).exists():
            return Movimiento_Prod.objects.filter(vale_e=self).count()
        if Vale_Salida_Almacen_Produccion.objects.filter(vale_movimiento=self).exists():
            return Vale_Salida_Almacen_Produccion.objects.filter(vale_movimiento=self).count()
        if Vale_Salida_Almacen_Envasado.objects.filter(vale_movimiento= self).exists():
            return Vale_Salida_Almacen_Envasado.objects.filter(vale_movimiento= self).count()
        if Prod_Inv_MP.objects.filter(vale=self).exists():
            print('Solicitud de produccion')
            return Prod_Inv_MP.objects.filter(vale=self).count()
        print('0')

    @property
    def produccion_asociada(self):
        from produccion.models import Prod_Inv_MP
        if Prod_Inv_MP.objects.filter(vale=self).exists():
            mp = Prod_Inv_MP.objects.filter(vale=self).first()
            return mp.lote_prod.id
        if Vale_Salida_Almacen_Produccion.objects.filter(vale_movimiento=self).exists():
            mp = Vale_Salida_Almacen_Produccion.objects.filter(vale_movimiento=self).first()
            return mp.solicitud_produccion.id
        
#Relación mucho a mucho de movimiento con Produccion
class Vale_Salida_Almacen_Produccion(ModeloBase):
    from produccion.models import Produccion
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
        related_name='salidas_produccion',
        verbose_name="Movimiento"
    )

#Relación mucho a mucho de movimiento con envasado
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
        null=True, blank=False, related_name="movimientos")
    cantidad = models.DecimalField(max_digits=6, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")
    #entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")

    def __str__(self):
        entrada = 'Entrada ' if self.vale.entrada else 'Salida '
        if self.materia_prima:
            return f'{entrada} de {self.materia_prima.nombre} en {self.vale.almacen.nombre}'
        else:
            return 'No hay materia prima en este movimiento'

#Relación mucho a mucho de vale con envase y embalaje 
class Movimiento_EE(ModeloBase):
    envase_embalaje = models.ForeignKey(EnvaseEmbalaje, on_delete=models.PROTECT,
        verbose_name="Envase o embalaje", null=True, blank=False,
    )
    vale_e = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=True, blank=False, related_name="movimientos_e")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")    
    #entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")

    def __str__(self):
        entrada = 'Entrada ' if self.vale_e.entrada else 'Salida '
        return f'{entrada} de {self.envase_embalaje.codigo_envase} en {self.vale_e.almacen.nombre}'

#Relación mucho a mucho de vale con producto     
class Movimiento_Prod(ModeloBase):
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT,
        verbose_name="Productos",
        null=True, blank=False,
    )
    vale_e = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=True, blank=False, related_name="movimientos_prod")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")
    #entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")

    def __str__(self):
        entrada = 'Entrada ' if self.vale_e.entrada else 'Salida '
        return f'{entrada} de {self.producto.nombre_comercial} en {self.vale_e.almacen.nombre}'

#Relación mucho a mucho de vale con insumo
class Movimiento_Ins(ModeloBase):
    insumo = models.ForeignKey(Insu, on_delete=models.PROTECT,
        verbose_name="Insumos", null=True, blank=False,
    )
    vale_e = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale asociado a este movimiento",
        null=True, blank=False, related_name="movimientos_i")
    cantidad = models.DecimalField(max_digits=4, decimal_places=2, default=1.00, verbose_name="Cantidad del movimiento")    
    #entrada = models.BooleanField(default=True, verbose_name="Verdadero: alta en el almacén")

    def __str__(self):
        entrada = 'Entrada ' if self.vale_e.entrada else 'Salida '
        return f'{entrada} de {self.insumo.nombre} en {self.vale_e.almacen.nombre}'
