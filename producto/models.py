from django.core.exceptions import ValidationError
from django.db import models
from bases.bases.models import ModeloBase
from ficha_tecnica.models import FichaTecnica
from nomencladores.almacen.models import Almacen


class Producto(ModeloBase):
    codigo_producto = models.CharField(
        max_length=20,
        verbose_name="Código del producto",
        null=True,
        blank=True,
        unique=True  # Asegura que el código del producto sea único
    )

    nombre_comercial = models.CharField(
        max_length=255,
        verbose_name="Nombre comercial",
        null=False,
        blank=False  # Asegura que este campo no esté vacío
    )

    product_final = models.BooleanField(
        default=True,
        verbose_name="Producto final"
    )

    cantidad_alm = models.IntegerField(
        default=0,
        verbose_name="Cantidad almacenada",
        null=False,
        blank=False
    )

    ficha_tecnica_folio = models.OneToOneField(
        FichaTecnica,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Ficha técnica folio"
    )

    ficha_costo = models.FileField(
        upload_to='fichas_costo/',  # Especifica un directorio para subir archivos
        null=True,
        blank=True,  # Cambiar a False si es obligatorio
        verbose_name="Ficha de costo"
    )

    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        verbose_name="Almacén",
        null=False
    )

    def __str__(self):
        return self.nombre_comercial

    def clean(self):
        # Validaciones adicionales
        if self.cantidad_alm < 0:
            raise ValidationError("La cantidad almacenada no puede ser negativa.")


