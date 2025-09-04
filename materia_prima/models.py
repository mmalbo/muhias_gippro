from django.db import models
from bases.bases.models import ModeloBase
from .choices import ESTADOS, Tipo_mat_prima, obtener_tipos_materia_prima
from nomencladores.almacen.models import Almacen
from django.core.exceptions import ValidationError

class MateriaPrima(ModeloBase): 
    # Analizar si hay que especificarlo o se autogenera
    codigo = models.CharField(
        verbose_name="Código de la materia prima",
        unique=True,
        null=False,
        max_length=20
    )
    
    estado = models.CharField(
        choices=ESTADOS,
        max_length=255,
        null=False,
        default='comprado',
        verbose_name='Estado'
    )

    tipo_materia_prima = models.CharField(
        max_length=20,
        choices=obtener_tipos_materia_prima(),
        default='otros',
        verbose_name='Tipo de materia prima')

    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre",
        null=False,
        blank=False,
    )

    conformacion = models.CharField(
        max_length=255,
        verbose_name="Conformación",
        null=False,
    )

    unidad_medida = models.CharField(
        max_length=255,
        verbose_name="Unidad de medida",
        null=False
    )

    concentracion = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        verbose_name="Concentración",
    )

    costo = models.FloatField(
        null=True,
        blank=False,
        default=0,
        verbose_name="Costo",
    )

    # La materia prima puede estar en más de un almacen. Por lo que aquí no pinta nada el almacen  

    ficha_tecnica = models.FileField(
        upload_to='fichas_tecnicas/',
        null=True,
        editable=True,
        verbose_name="Ficha técnica"
    )

    hoja_seguridad = models.FileField(
        upload_to='hojas_seguridad/',
        null=True,
        editable=True,
        verbose_name="Hoja de seguridad"
    )

    class Meta:
        verbose_name = 'Materia Prima'
        verbose_name_plural = 'Materias Primas'
        ordering = ['tipo_materia_prima']        

    def __str__(self):
        return self.nombre

    def get_ficha_tecnica_name(self):
        return self.ficha_tecnica.name if self.ficha_tecnica else ''

    def get_hoja_seguridad_name(self):
        return self.hoja_seguridad.name if self.hoja_seguridad else ''

    def save(self, *args, **kwargs):
        # Actualizar choices antes de guardar
        self._meta.get_field('tipo_materia_prima').choices = obtener_tipos_materia_prima()
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.costo < 0:
            raise ValidationError('El costo no puede ser negativo.')