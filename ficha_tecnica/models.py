from django.db import models
from bases.bases.models import ModeloBase


class FichaTecnica(ModeloBase):
    fecha_elaboracion = models.DateField(
      # editable=False,
        verbose_name="Fecha de elaboración",
        null=False,
    )
    institucion = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Institución",
        null=True,
        blank=True,
    )
    nombre_quimico = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Nombre químico",
        null=True,
        blank=True,
    )
    nombre_comercial = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Nombre comercial",
        null=True,
        blank=True,
    )
    formula_quimica = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Fórmula química",
        null=False,
    )
    presentacion = models.IntegerField(
      # editable=False,
        verbose_name="Presentación",
        null=True,
        blank=True,
    )
    clasificacion = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Clasificación",
        null=False,
    )
    masa_molecular = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Masa molecular",
        null=False,
    )
    parametro_fisioquimicp = models.CharField(
        max_length=255,
        # unique=True,
      # editable=False,
        verbose_name="Parámetro fisioquímico",
        null=False,
    )

    especificacion_fisioquimica = models.IntegerField(
      # editable=False,
        verbose_name="Especificación Fisioquímica",
        null=True,
        blank=True,
    )

    usos_identificados = models.TextField(
        # unique=True,
      # editable=False,
        verbose_name="Usos identificados",
        null=False,
    )
    condiciones_almacenaje = models.TextField(
        # unique=True,
      # editable=False,
        verbose_name="Condiciones de almacenaje",
        null=False,
    )

    precaucion = models.TextField(
        # unique=True,
      # editable=False,
        verbose_name="Precaución",
        null=True,
        blank=True,
    )
    garantia = models.TextField(
        # unique=True,
      # editable=False,
        verbose_name="Garantía",
        null=True,
        blank=True,
    )
