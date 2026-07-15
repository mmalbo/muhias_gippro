from django.db import models
from bases.bases.models import ModeloBase

CHOICE_MONEDAS = (
    ('USD', 'USD'),
    ('CUP', 'CUP'),
    ('MLC', 'MLC'),
    ('EUR', 'EUR'),
    ('MXN', 'MXN')
)

class FichaCosto(ModeloBase):
    costo_x_itro = models.FloatField(verbose_name="Costo por litro", null=False, default=0,)
    utilidad = models.FloatField(null=False, default=0.30, verbose_name="Utilidad",)
    monto_cambio = models.FloatField(null=False, default=1, verbose_name="Cambio de referencia",)
    activo = models.BooleanField(default=True, verbose_name="Ficha activa",)

    class Meta:
        verbose_name = "Ficha de Costo"
        verbose_name_plural = "Fichas de Costo"
        ordering = ['-fecha_creacion']

    @property
    def mes(self):
        """Retorna el mes de creación en formato 'Enero 2024'"""
        return self.fecha_creacion.strftime('%B %Y')
    
    @property
    def mes_codigo(self):
        """Retorna el mes en formato '2024-01' para filtros"""
        return self.fecha_creacion.strftime('%Y-%m')

