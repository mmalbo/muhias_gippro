from django.db import models
from django.core.exceptions import ValidationError
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
import os


def factura_upload_to(instance, filename):
    folder_name = 'materia_prima'
    # Obtenemos el tipo de adquisición
    """     if isinstance(instance, MateriaPrimaAdquisicion):
        folder_name = 'materia_prima'
    elif isinstance(instance, EnvaseAdquisicion):
        folder_name = 'envase'
    elif isinstance(instance, InsumosAdquisicion):
        folder_name = 'insumos'
    else:
        raise ValidationError("Tipo de adquisición no válido") """

    # Retornamos la ruta completa donde se guardará el archivo
    return os.path.join('facturas', folder_name, filename)


class Adquisicion(models.Model):
    fecha_compra = models.DateField(
        verbose_name="Fecha de la compra",
        null=True,
        editable=True
    )
    factura = models.FileField(
        verbose_name="Factura",
        null=True, blank=True,
        upload_to=factura_upload_to  # Usamos la función definida
    )
    importada = models.BooleanField(
        verbose_name="Importada",
        null=False, default=False
    )

    creado_en = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        return f"Compra #{self.id} - {self.fecha}"


class DetallesAdquisicion(models.Model):
    adquisicion = models.ForeignKey(Adquisicion, on_delete=models.CASCADE, related_name='detalles')
    materia_prima = models.ForeignKey(
        MateriaPrima, on_delete=models.CASCADE,  # Cambiado a PROTECT
        verbose_name="Materia prima adquirida"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=1)

    def __str__(self):
        return f"{self.materia_prima.nombre} - {self.adquisicion.fecha_compra}"
    