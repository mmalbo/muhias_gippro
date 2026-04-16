from django.core.exceptions import ValidationError
from django.db import models
from bases.bases.models import ModeloBase
from ficha_tecnica.models import FichaTecnica

from django.db.models import Sum
from utils.utils import eliminar_tildes

class Producto(ModeloBase):
    codigo_producto = models.CharField( max_length=20, verbose_name="Código del producto", null=True,
        blank=True, unique=True  # Asegura que el código del producto sea único
    )

    codigo_3l = models.CharField(max_length=3, verbose_name="Código de 3 letras del producto", null=True,
        blank=True, default='XXX' 
    )

    nombre_comercial = models.CharField( max_length=255, verbose_name="Nombre comercial", null=False,
        blank=False 
    )

    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    ficha_tecnica_folio = models.FileField(upload_to='fichas_tecnicas/', null=True, blank=True, 
        verbose_name="Ficha técnica"
    )    # models.OneToOneField( FichaTecnica, on_delete=models.CASCADE, null=True, verbose_name="Ficha técnica folio" )

    ficha_costo = models.FileField( upload_to='fichas_costo/',  # Especifica un directorio para subir archivos
        null=True, blank=True,  # Cambiar a False si es obligatorio
        verbose_name="Ficha de costo" )

    prod_base = models.BooleanField(default=False, verbose_name="Producto base")
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['codigo_producto']
        indexes = [
            models.Index(fields=['codigo_producto']),
        ]
    
    def __str__(self):
        return f"{self.codigo_producto} - {self.nombre_comercial}"

    @property
    def cantidad_total(self):
        """
        Calcula la cantidad total de este producto en todos los almacenes
        """
        total = self.inventarios_prod.aggregate(
            total=Sum('cantidad')
        )['total']
        return total if total is not None else 0

    def clean(self):
        """Validaciones a nivel de modelo"""
        super().clean()
        errors = {}
        # Validar unicidad del nombre comercial por formato
        if Producto.objects.filter(
            nombre_comercial=self.nombre_comercial,
        ).exclude(pk=self.pk).exists():
            errors['nombre_comercial'] = 'Ya existe un producto en inventario con este nombre'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Validaciones adicionales al guardar"""
        try:
            self.full_clean()
        except ValidationError as e:
            print(eliminar_tildes(e))
        print("Guardando producto")
        super().save(*args, **kwargs)
