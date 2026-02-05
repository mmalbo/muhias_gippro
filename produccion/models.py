from decimal import Decimal
import re
from django.core.validators import FileExtensionValidator
from django.db import models
import os
from datetime import date, datetime, timezone
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
    lote = models.CharField(unique=True, null=False, blank=False, max_length=20, verbose_name="Lote")

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

    observaciones_cancelacion = models.TextField(blank=True,null=True,
        verbose_name="Observaciones de Cancelación/Detención"
    )
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lote {self.lote} - {self.catalogo_producto.nombre_comercial}"

    @property
    def total_materias_primas(self):
        return self.inventarios_prod.count()

    @property
    def tiene_prueba_quimica(self):
        """Verifica si ya tiene una prueba química creada"""
        return self.pruebas_quimicas.exists()

    @staticmethod
    def generar_lote(catalogo_producto, planta, cantidad_estimada=None):
        """
        Genera lote con formato: YYMMDD-XXX-XXXX-AG
        Donde:
        - YYMMDD: Año (2 dígitos), Mes (2 dígitos), Día (2 dígitos)
        - XXX: 3 letras del producto (extraídas del nombre comercial)
        - XXXX: 4 dígitos para litros de volumen (ej: 0020)
        - AG: Sufijo fijo para 'A Granel'
        """
        # 1. Obtener fecha en formato YYMMDD
        fecha_actual = datetime.now()
        fecha_codigo = fecha_actual.strftime('%y%m%d')  # YYMMDD
        
        # 2. Obtener 3 letras del producto
        if catalogo_producto.nombre_comercial:
            # Tomar las primeras 3 letras mayúsculas, eliminar espacios y caracteres especiales
            nombre = catalogo_producto.nombre_comercial.upper()
            # Filtrar solo letras
            letras = re.sub(r'[^A-Z]', '', nombre)
            
            if len(letras) >= 3:
                codigo_producto = letras[:3]
            elif len(letras) > 0:
                # Si tiene menos de 3 letras, completar con X
                codigo_producto = letras + 'X' * (3 - len(letras))
            else:
                # Si no tiene letras, usar XXX
                codigo_producto = 'XXX'
        else:
            codigo_producto = 'XXX'
        
        # 3. Obtener 4 dígitos para litros de volumen
        if cantidad_estimada is not None:
            try:
                # Convertir a entero y formatear a 4 dígitos
                litros = int(float(cantidad_estimada))
                codigo_litros = f"{litros:04d}"
            except (ValueError, TypeError):
                codigo_litros = "0000"
        else:
            codigo_litros = "0000"
        
        # 4. Sufijo fijo
        sufijo = "AG"  # A Granel
        
        # 5. Construir lote completo
        lote = f"{fecha_codigo}-{codigo_producto}-{codigo_litros}-{sufijo}"
        return lote
    
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

    def reutilizar_como_base(self, usuario, nuevo_producto_id=None):
        """
        Reutiliza una producción rechazada como base para nueva producción
        Args:
            usuario: Usuario que realiza la reutilización
            nuevo_producto_id: ID del nuevo producto (opcional, si es None usa el mismo)
            ajustes: dict con ajustes específicos (porcentajes de ajuste, etc.)
        Returns:
            Nueva producción creada
        """
        
        with transaction.atomic():
            # 1. Determinar el nuevo producto
            if nuevo_producto_id:
                nuevo_producto = Producto.objects.get(id=nuevo_producto_id)
            else:
                nuevo_producto = None
                        
            # 3. Crear nueva producción
            nueva_produccion = self._crear_nueva_desde_rechazada(
                usuario, 
                nuevo_producto,
                factor_ajuste
            )
            
            # 5. Actualizar estado de la producción original
            self._marcar_como_reutilizada(usuario, nueva_produccion)
            
            # 6. Registrar en historial
            self.registrar_reutilizacion(usuario, nueva_produccion)
            
            return nueva_produccion
    
    def _crear_nueva_desde_rechazada(self, usuario, nuevo_producto, factor_ajuste):
        """Crea nueva producción basada en la rechazada"""
        # Generar nuevo lote
        nuevo_lote = self._generar_lote_reutilizacion(nuevo_producto)
        
        # Calcular nueva cantidad (puede ajustarse)
        nueva_cantidad = self.cantidad_estimada * factor_ajuste
        
        # Crear producción
        nueva_produccion = Produccion.objects.create(
            lote=nuevo_lote,
            catalogo_producto=nuevo_producto,
            prod_result=self.prod_result,  # Puede ser diferente según el caso
            cantidad_estimada=nueva_cantidad,
            costo=Decimal('0'),  # Se recalculará con las materias primas
            planta=self.planta,
            estado='Planificada',
            # Campos que indican que viene de una reutilización
            produccion_base=self,
            es_reutilizacion=True,
            fecha_reutilizacion=timezone.now(),
            usuario_reutilizacion=usuario
        )
        
        return nueva_produccion
    
    def _reutilizar_materias_primas(self, nueva_produccion, ajustar, factor_ajuste):
        """Reutiliza las materias primas de la producción rechazada"""
        materias_originales = Prod_Inv_MP.objects.filter(lote_prod=self)
        
        for mp in materias_originales:
            # Calcular nueva cantidad (si hay ajuste)
            if ajustar:
                nueva_cantidad = mp.cantidad_materia_prima * factor_ajuste
            else:
                nueva_cantidad = mp.cantidad_materia_prima
            
            # Verificar disponibilidad en inventario
            try:
                inventario = Inv_Mat_Prima.objects.get(
                    materia_prima=mp.inv_materia_prima,
                    almacen=mp.almacen
                )
                
                if inventario.cantidad < nueva_cantidad:
                    # Si no hay suficiente, crear una entrada de ajuste
                    # o buscar en otro almacén
                    almacen_alternativo = self._buscar_almacen_alternativo(
                        mp.inv_materia_prima, 
                        nueva_cantidad
                    )
                    if almacen_alternativo:
                        almacen_uso = almacen_alternativo
                    else:
                        # Si no hay en ningún almacén, usar el mismo pero marcar para resurtir
                        almacen_uso = mp.almacen
                        nueva_produccion.necesita_resurtimiento = True
                else:
                    almacen_uso = mp.almacen
                
                # Crear relación en la nueva producción
                Prod_Inv_MP.objects.create(
                    lote_prod=nueva_produccion,
                    inv_materia_prima=mp.inv_materia_prima,
                    cantidad_materia_prima=nueva_cantidad,
                    almacen=almacen_uso,
                    vale=None,  # Se creará al confirmar
                    es_reutilizado=True,
                    produccion_origen=mp
                )
                
            except Inv_Mat_Prima.DoesNotExist:
                # Si no existe inventario, marcar para resurtimiento
                Prod_Inv_MP.objects.create(
                    lote_prod=nueva_produccion,
                    inv_materia_prima=mp.inv_materia_prima,
                    cantidad_materia_prima=nueva_cantidad,
                    almacen=mp.almacen,
                    necesita_resurtimiento=True,
                    es_reutilizado=True,
                    produccion_origen=mp
                )
    
    def _buscar_almacen_alternativo(self, materia_prima, cantidad_necesaria):
        """Busca la materia prima en otros almacenes"""
        inventarios = Inv_Mat_Prima.objects.filter(
            materia_prima=materia_prima,
            cantidad__gte=cantidad_necesaria
        ).exclude(almacen=self.almacen).order_by('cantidad')
        
        if inventarios.exists():
            return inventarios.first().almacen
        return None
    
    def _generar_lote_reutilizacion(self, nuevo_producto=None):
        """Genera lote para producción reutilizada"""
        fecha_actual = timezone.now().strftime('%y%m%d')
        
        # Determinar código de producto
        if nuevo_producto:
            producto = nuevo_producto
        else:
            producto = self.catalogo_producto
        
        # Obtener 3 letras del producto
        nombre = str(producto.nombre_comercial or '').upper()
        letras = re.sub(r'[^A-Z]', '', nombre)
        
        if len(letras) >= 3:
            codigo_producto = letras[:3]
        elif len(letras) > 0:
            codigo_producto = letras + 'X' * (3 - len(letras))
        else:
            codigo_producto = 'XXX'
        
        # Usar cantidad de la producción original para el código
        cantidad_codigo = f"{int(self.cantidad_estimada):04d}"
        
        # Buscar secuencial para el día
        producciones_hoy = Produccion.objects.filter(
            lote__startswith=f"{fecha_actual}-{codigo_producto}-{cantidad_codigo}-REU"
        ).count()
        
        if producciones_hoy > 0:
            return f"{fecha_actual}-{codigo_producto}-{cantidad_codigo}-REU{producciones_hoy + 1:02d}"
        else:
            return f"{fecha_actual}-{codigo_producto}-{cantidad_codigo}-REU"
    
    def _marcar_como_reutilizada(self, usuario, nueva_produccion):
        """Marca la producción original como reutilizada"""
        self.estado = 'Reutilizada'
        self.produccion_derivada = nueva_produccion
        self.fecha_reutilizacion = timezone.now()
        self.usuario_reutilizacion = usuario
        self.save()
    
    def registrar_reutilizacion(self, usuario, nueva_produccion):
        """Registra la reutilización en el historial"""
        from django.contrib.admin.models import LogEntry, CHANGE
        
        # Registrar en producción original
        LogEntry.objects.log_action(
            user_id=usuario.id,
            content_type_id=ContentType.objects.get_for_model(self).pk,
            object_id=self.id,
            object_repr=str(self),
            action_flag=CHANGE,
            change_message=f"Reutilizada como base para nueva producción {nueva_produccion.lote}"
        )
        
        # Registrar en nueva producción
        LogEntry.objects.log_action(
            user_id=usuario.id,
            content_type_id=ContentType.objects.get_for_model(nueva_produccion).pk,
            object_id=nueva_produccion.id,
            object_repr=str(nueva_produccion),
            action_flag=CHANGE,
            change_message=f"Creada reutilizando producción {self.lote}"
        )
    
    @property
    def puede_ser_reutilizada(self):
        """
        Determina si esta producción puede ser reutilizada como base
        Solo producciones rechazadas o con problemas pueden reutilizarse
        """
        estados_reutilizables = [
            'Concluida-Rechazada',
            'Cancelada'  # Solo si se canceló por razones específicas
        ]
        
        # Verificar que no haya sido ya reutilizada
        no_reutilizada_anteriormente = not hasattr(self, 'produccion_derivada') or self.produccion_derivada is None
        
        return self.estado in estados_reutilizables and no_reutilizada_anteriormente
    
    @property
    def materias_primas_reutilizables(self):
        """Retorna las materias primas que pueden ser reutilizadas"""
        return Prod_Inv_MP.objects.filter(lote_prod=self)

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

    cantidad_materia_prima = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Cantidad de la materia prima",)

    estado = estado = models.CharField(verbose_name='Estado', default='Solicitada', max_length=50, choices=CHOICE_ESTADO_SOL, blank=False, null=False )

    vale = models.ForeignKey(Vale_Movimiento_Almacen, on_delete=models.PROTECT,
        verbose_name="Vale de solicitud asociado a esta producción",
        null=True, blank=False, related_name="mp_produccion")

class ParametroPrueba(models.Model):
    """Catálogo de parámetros que se miden en las pruebas químicas"""
    UNIDADES_MEDIDA = [
        ('PH', 'pH'),
        ('%', 'Porcentaje'),
        ('Kg/L', 'Kilogramos por Litro'),
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
        return f"Prueba {self.produccion.lote} - {self.fecha_prueba}"
    
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
    cumplimiento = models.BooleanField()  # Calculado automáticamente o puesto en el caso de los roganolepticos
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
        print("En cumple especificacion")
        if self.parametro.valor_minimo is not None and Decimal(self.valor_medido) <= self.parametro.valor_minimo:
            return False
        if self.parametro.valor_maximo is not None and Decimal(self.valor_medido) >= self.parametro.valor_maximo:
            return False
        return True
    
    def save(self, *args, **kwargs):
        # Calcular cumplimiento automáticamente antes de guardar
        if self.parametro.es_numerico(): #tipo != "organoleptico":
            self.cumplimiento = self.cumple_especificacion
        super().save(*args, **kwargs)