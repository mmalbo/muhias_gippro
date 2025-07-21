from django.db import models
from bases.bases.models import ModeloBase
from .tipo_materia_prima.models import TipoMateriaPrima
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

    ESTADOS = [
        ('comprado', 'Comprado'),
        ('en_almacen', 'En almacén'),
        ('reservado', 'Reservado'),
    ]

    # Este estado no debe ser de materia prima sino de una adquisición. No entiendo por que reservado aqui
    estado = models.CharField(
        choices=ESTADOS,
        max_length=255,
        null=False,
        default='comprado',
        verbose_name='Estado'
    )

    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre",
        null=False,
        blank=False,
    )

    tipo_materia_prima = models.ForeignKey(
        TipoMateriaPrima, on_delete=models.CASCADE,
        null=False,
        verbose_name='Tipo de materia prima'
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

    """ cantidad_almacen = models.IntegerField(
        null=True,
        blank=False,
        default=0,
        verbose_name="Cantidad",
    ) """

    costo = models.FloatField(
        null=True,
        blank=False,
        default=0,
        verbose_name="Costo",
    )

    # La materia prima puede estar en más de un almacen. Por lo que aquí no pinta nada el almacen  
    """ almacen = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        null=False,
        verbose_name='Almacen ubicación'
    ) """

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

    def __str__(self):
        return self.nombre

    def get_ficha_tecnica_name(self):
        return self.ficha_tecnica.name if self.ficha_tecnica else ''

    def get_hoja_seguridad_name(self):
        return self.hoja_seguridad.name if self.hoja_seguridad else ''

    def clean(self):
        """ if self.cantidad_almacen < 0:
            raise ValidationError('La cantidad en almacén no puede ser negativa.') """
        if self.costo < 0:
            raise ValidationError('El costo no puede ser negativo.')