from django.core.validators import FileExtensionValidator
from django.db import models
import os
from datetime import datetime, timezone
from bases.bases.models import ModeloBase
from nomencladores.planta.models import Planta
from produccion.choices import CHOICE_ESTADO_PROD, CHOICE_ESTADO_SOL, TIPOS_PARAMETRO, ESTADOS_PRUEBA
from inventario.models import Inv_Mat_Prima
from movimientos.models import Vale_Movimiento_Almacen
from producto.models import Producto
from materia_prima.models import MateriaPrima
from nomencladores.almacen.models import Almacen
from usuario.models import CustomUser
import uuid

def generate_unique_filename(instance, filename):
    now = datetime.now()
    date_part = now.strftime('%Y%m%d%H%M%S')
    name_part, extension = os.path.splitext(filename)
    return f'pruebas_quimicas/{name_part}_{date_part}{extension}'

"""def ruta_archivo_pruebas(instance, filename):
    Generar ruta para archivos de pruebas químicas
    ext = filename.split('.')[-1]
    nombre_archivo = f"pruebas_{instance.produccion.lote}_{uuid.uuid4().hex[:8]}.{ext}"
    return f"pruebas_quimicas/{nombre_archivo}"""

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

    pruebas_quimicas_ext = models.FileField(upload_to=generate_unique_filename, null=True, blank=True, verbose_name="Pruebas químicas",
        validators=[FileExtensionValidator(allowed_extensions=['pdf','doc','docx','xls','xlsx','jpg','jpeg','png'])])

    prod_conform = models.BooleanField(null=True, blank=True, default=False, verbose_name="Producto Conforme",)

    costo = models.FloatField(null=False, blank=False, verbose_name="Costo",)

    planta = models.ForeignKey(Planta, on_delete=models.DO_NOTHING, null=False, verbose_name="Planta")

    estado = models.CharField(verbose_name='Estado', max_length=50, choices=CHOICE_ESTADO_PROD, blank=False, null=False )

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
        return self.estado in ['Planificada', 'Iniciando mezcla']

    def nombre_archivo_pruebas(self):
        """Retorna el nombre del archivo sin la ruta"""
        if self.pruebas_quimicas_ext:
            return os.path.basename(self.pruebas_quimicas_ext.name)
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
        MateriaPrima,  # Referencia al modelo completo
        on_delete=models.DO_NOTHING,
        verbose_name="Materia prima",
    )

    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.DO_NOTHING,
        null = True,
        verbose_name="Almacen de la materia prima"        
    )

    cantidad_materia_prima = models.IntegerField(
        null=False,
        blank=False,
        default=1,
        verbose_name="Cantidad de la materia prima",
    )

    estado = estado = models.CharField(verbose_name='Estado', default='Solicitada', max_length=50, choices=CHOICE_ESTADO_SOL, blank=False, null=False )

    vale = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale de solicitud asociado a esta producción",
        null=True, blank=False, related_name="mp_produccion")

class ParametroPrueba(models.Model):
    """Catálogo de parámetros que se miden en las pruebas químicas"""
    UNIDADES_MEDIDA = [
        ('PH', 'pH'),
        ('%', 'Porcentaje'),
        ('g/L', 'Gramos por Litro'),
        ('mg/L', 'Miligramos por Litro'),
        ('cps', 'Centipoise'),
        ('g/cm3', 'Gramos por cm³'),
        ('unidades', 'Unidades'),
        ('UFC/mL', 'UFC por mL'),
        ('mm', 'Milímetros'),
        ('segundos', 'Segundos'),
        ('minutos', 'Minutos'),
        ('Ninguna', 'Ninguna'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_PARAMETRO)
    unidad_medida = models.CharField(max_length=20, choices=UNIDADES_MEDIDA, default='Ninguna')
    descripcion = models.TextField(blank=True)
    metodo_ensayo = models.CharField(max_length=200, blank=True)  # Norma o método usado
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    valor_maximo = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    valor_objetivo = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        #db_table = 'parametro_prueba'
        verbose_name = 'Parámetro de Prueba'
        verbose_name_plural = 'Parámetros de Prueba'
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida})"

    def es_organoleptico(self):
        """Determina si el parámetro requiere evaluación manual"""
        if self.tipo in ['organoleptico']:
            return True
        else:
            return False
    
    def es_numerico(self):
        """Determina si el parámetro es numérico"""
        if self.tipo in ['fisico', 'quimico', 'microbiologico']:
            return True
        else:
            return False

class PruebaQuimica(models.Model):
    """Registro completo de una prueba química realizada"""
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nomenclador_prueba = models.CharField(max_length=100, null=True, blank=True)
    produccion = models.ForeignKey('Produccion', on_delete=models.CASCADE, related_name='pruebas_quimicas')
    fecha_prueba = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)  # Para productos con fecha de vencimiento
    #responsable = models.ForeignKey('CustomUser', on_delete=models.PROTECT, related_name='pruebas_realizadas')
    estado = models.CharField(max_length=20, choices=ESTADOS_PRUEBA, default='en_proceso')
    observaciones = models.TextField(blank=True)
    archivo_resultado = models.FileField(upload_to=generate_unique_filename, null=True, blank=True, 
                                         verbose_name="Archivo de Resultados" )
    # Resultado general
    resultado_final = models.BooleanField(null=True, blank=True)  # True=Aprobado, False=Rechazado
    fecha_aprobacion = models.DateField(auto_now_add=True)
    #aprobado_por = models.ForeignKey( 'CustomUser', on_delete=models.SET_NULL, null=True, blank=True, 
                                     #related_name='pruebas_aprobadas' )
    
    class Meta:
        #db_table = 'prueba_quimica'- {self.fecha_prueba.date()}
        verbose_name = 'Prueba Química'
        verbose_name_plural = 'Pruebas Químicas'
        ordering = ['-fecha_prueba']
    
    def __str__(self):
        return f"Prueba {self.produccion.lote} - {self.fecha_prueba.date()}"
    
    def nombre_archivo(self):
        if self.archivo_resultado:
            return os.path.basename(self.archivo_resultado.name)
        return None
    
    def calcular_resultado_final(self):
        """Calcula el resultado final basado en los detalles de la prueba"""
        detalles = self.detalles.all()
        if not detalles.exists():
            return None
        
        # Si algún parámetro obligatorio está fuera de especificación, rechazar
        for detalle in detalles:
            if detalle.parametro.obligatorio and not detalle.cumple_especificacion:
                return False
        
        # Si todos los parámetros obligatorios cumplen, aprobar
        return all(detalle.cumple_especificacion for detalle in detalles if detalle.parametro.obligatorio)
    
    def aprobar(self, usuario):
        """Marca la prueba como aprobada"""
        self.estado = 'aprobada'
        self.resultado_final = True
        self.fecha_aprobacion = timezone.now()
        #self.aprobado_por = usuario
        self.save()
    
    def rechazar(self, usuario):
        """Marca la prueba como rechazada"""
        self.estado = 'rechazada'
        self.resultado_final = False
        self.fecha_aprobacion = timezone.now()
        self.aprobado_por = usuario
        self.save()

class DetallePruebaQuimica(models.Model):
    """Detalle de cada parámetro medido en la prueba química"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prueba = models.ForeignKey('PruebaQuimica', on_delete=models.CASCADE, related_name='detalles')
    parametro = models.ForeignKey('ParametroPrueba', on_delete=models.PROTECT)
    valor_medido = models.CharField(max_length=100)  #DecimalField(max_digits=10, decimal_places=3)
    cumplimiento = models.BooleanField()  # Calculado automáticamente
    observaciones = models.TextField(blank=True)
    
    class Meta:
        #db_table = 'detalle_prueba_quimica'
        verbose_name = 'Detalle de Prueba Química'
        verbose_name_plural = 'Detalles de Pruebas Químicas'
        unique_together = ['prueba', 'parametro']

    def __str__(self):
        return f"{self.parametro.nombre}: {self.valor_medido}"
   
    @property
    def cumple_especificacion(self):
        """Calcula si el valor medido cumple con las especificaciones"""
        if self.parametro.valor_minimo is not None and self.valor_medido <= self.parametro.valor_minimo:
            return False
        if self.parametro.valor_maximo is not None and self.valor_medido >= self.parametro.valor_maximo:
            return False
        return True
    
    def save(self, *args, **kwargs):
        # Calcular cumplimiento automáticamente antes de guardar
        if self.parametro.tipo != "organoleptico":
            self.cumplimiento = self.cumple_especificacion
        super().save(*args, **kwargs)