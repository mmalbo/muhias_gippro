from datetime import timezone
import os
from django.core.validators import FileExtensionValidator
from django.db import models
from bases.bases.models import ModeloBase
from produccion.choices import ESTADOS_ENV
from producto.models import Producto
from inventario.models import Inv_Producto, Inv_Envase, Inv_Insumos
from envase_embalaje.models import EnvaseEmbalaje
from usuario.models import CustomUser
from django.core.validators import MinValueValidator
import uuid

# Create your models here.

class SolicitudEnvasado(ModeloBase):
    """Modelo para solicitudes de envasado"""
    folio = models.CharField(max_length=20, unique=True, editable=False)
    lote_produccion_origen = models.ForeignKey(Inv_Producto, on_delete=models.PROTECT,
                                              related_name='solicitudes_envasado')
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    fecha_solicitud = models.DateField(auto_now_add=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    
    solicitante = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='solicitudes_envasado')
    estado = models.CharField(max_length=20, choices=ESTADOS_ENV, default='pendiente')
    
    observaciones = models.TextField(blank=True)
    producto_destino = models.ForeignKey(Producto, on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='solicitudes_envasado_destino')
    lote_destino = models.ForeignKey(Inv_Producto, on_delete=models.PROTECT,
                                    null=True, blank=True,
                                    related_name='solicitudes_envasado_destino')
    unidades_producidas = models.PositiveIntegerField(null=True, blank=True)
    cantidad_perdida = models.DecimalField(max_digits=10, decimal_places=2, 
                                          null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
     
    class Meta:
        ordering = ['-fecha_solicitud']
        permissions = [
            ('aprobar_envasado', 'Puede aprobar solicitudes de envasado'),
            ('ejecutar_envasado', 'Puede ejecutar el proceso de envasado'),
        ]
    
    def save(self, *args, **kwargs):
        if not self.folio:
            # Generar folio automático
            year = timezone.now().year
            month = timezone.now().month
            last_solicitud = SolicitudEnvasado.objects.filter(
                folio__startswith=f'ENV-{year}{month:02d}'
            ).order_by('folio').last()
            
            if last_solicitud:
                last_number = int(last_solicitud.folio.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.folio = f'ENV-{year}{month:02d}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.folio} - {self.lote_produccion_origen.producto.nombre_comercial}"

class DetalleEnvasado(ModeloBase):
    """Detalle de qué envases se van a utilizar"""
    solicitud = models.ForeignKey(SolicitudEnvasado, on_delete=models.CASCADE)
    presentacion = models.ForeignKey(Inv_Envase, on_delete=models.PROTECT)
    cantidad_unidades = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    class Meta:
        unique_together = ['solicitud', 'presentacion']

    def __str__(self):
        return f"{self.presentacion.envase.nombre} - {self.cantidad_unidades} {self.presentacion.almacen}"

class ConsumoInsumoEnvasado(ModeloBase):
    """Registro de insumos utilizados en el envasado"""
    solicitud = models.ForeignKey(SolicitudEnvasado, on_delete=models.CASCADE, related_name='consumos')
    insumo = models.ForeignKey(Inv_Insumos, on_delete=models.PROTECT)
    cantidad_unidades = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ['solicitud', 'insumo']
    
    def __str__(self):
        return f"{self.insumo.insumos.nombre} - {self.cantidad_unidades} {self.insumo.almacen}"