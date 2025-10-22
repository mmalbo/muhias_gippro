from django.db import models
from django.core.exceptions import ValidationError
from materia_prima.models import MateriaPrima
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
from nomencladores.almacen.models import Almacen
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
    tipo_adquisicion = models.CharField(
        verbose_name="Tipo de adquisición",
        null=False, default="mp", max_length=10,
    )
    creado_en = models.DateTimeField(auto_now_add=True, null=True)

    registrada = models.BooleanField(
        verbose_name="Recibida en almacén",
        null=False, default=False
    ) 
    
    def __str__(self):
        return f"Compra #{self.id} - {self.fecha_compra}"
    
    @property
    def cantidad_mprimas(self):
        print(self.id)
        cantidad = DetallesAdquisicion.objects.filter(adquisicion=self.id).count()
        print(cantidad)
        return cantidad
    
    @property
    def cantidad_envases(self):
        print(self.id)
        detalles = DetallesAdquisicionEnvase.objects.filter(adquisicion__id=self.id)
        print(detalles)
        cantidad = DetallesAdquisicionEnvase.objects.filter(adquisicion__id=self.id).count()
        print(cantidad)
        return cantidad
    
    @property
    def cantidad_insumos(self):
        cantidad = DetallesAdquisicionInsumo.objects.filter(adquisicion=self.id).count()
        print(cantidad)
        return cantidad
    
class DetallesAdquisicion(models.Model):
    adquisicion = models.ForeignKey(Adquisicion, on_delete=models.CASCADE, null=True, related_name='detalles')
    materia_prima = models.ForeignKey(
        MateriaPrima, null=True, on_delete=models.CASCADE,  # Cambiado a PROTECT
        verbose_name="Materia prima adquirida"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=1)
    almacen = models.ForeignKey(
        Almacen, on_delete=models.CASCADE,  # Cambiado a PROTECT
        null=True,
        verbose_name="Almacén donde se ubicará la materia prima",
        related_name='detalles_adquisicion'
    )
    recibida = models.BooleanField(
        verbose_name="Recibida en almacén",
        null=False, default=False
    )

    def __str__(self):
        return f"{self.materia_prima.nombre} - {self.adquisicion.fecha_compra}"
    
class DetallesAdquisicionEnvase(models.Model):
    adquisicion = models.ForeignKey(Adquisicion, on_delete=models.CASCADE, related_name='detalles_envases')
    envase_embalaje = models.ForeignKey(
        EnvaseEmbalaje, null=True, on_delete=models.CASCADE,  # Cambiado a PROTECT
        verbose_name="Envase o embalaje adquirida"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=1)
    almacen = models.ForeignKey(
        Almacen, on_delete=models.CASCADE,  # Cambiado a PROTECT
        null=True,
        verbose_name="Almacén donde se ubicará el envase o producto para el embalaje"
    )
    recibida = models.BooleanField(
        verbose_name="Recibida en almacén",
        null=False, default=False
    )

    def __str__(self):
        return f"{self.envase_embalaje.codigo_envase} - {self.adquisicion.fecha_compra}"
    
class DetallesAdquisicionInsumo(models.Model):
    adquisicion = models.ForeignKey(Adquisicion, on_delete=models.CASCADE, related_name='detalles_insumos')
    insumo = models.ForeignKey(
        InsumosOtros, on_delete=models.CASCADE,  # Cambiado a PROTECT
        verbose_name="Insumo adquirido"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad", null=False, default=1)
    almacen = models.ForeignKey(
        Almacen, on_delete=models.CASCADE,  # Cambiado a PROTECT
        null=True,
        verbose_name="Almacén donde se ubicará el insumo"
    )
    recibida = models.BooleanField(
        verbose_name="Recibida en almacén",
        null=False, default=False
    )

    def __str__(self):
        return f"{self.insumo.nombre} - {self.adquisicion.fecha_compra}"
    
