from django.db import models, transaction
from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from django.core.exceptions import ValidationError

def validate_color(value):
    """
    Valida que el nombre del color tenga al menos 3 caracteres.
    """
    try:
        # Obtener la instancia de Color usando el UUID (value)
        color_instance = Color.objects.get(id=value)
    except Color.DoesNotExist:
        raise ValidationError("El color seleccionado no existe.")

    # Validar la longitud del nombre del color
    if len(color_instance.nombre) < 3:
        raise ValidationError("El nombre del color debe tener al menos 3 caracteres.")

class Tapa(TipoEnvaseEmbalaje):
   
    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        blank=False,
        null=False,  # Cambiado a False para que el color sea obligatorio
        verbose_name="Color",
        validators=[validate_color]  # Aplicar la validación aquí
    )
    descripcion = models.TextField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    
    class Meta:
        verbose_name = "Tapa"
        verbose_name_plural = "Tapas"
        ordering = ['nombre']  # Ordenar por nombre por defecto

    def __str__(self):
        return self.nombre

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Verificar si el objeto ya existe en la base de datos
        if self.pk:  # Si el objeto ya tiene un ID (ya existe)
            # Obtener el objeto actual desde la base de datos
            tapa_actual = Tapa.objects.get(pk=self.pk)

            # Verificar si el nombre o el color han cambiado
            if self.nombre != tapa_actual.nombre:
                tapa_actual.nombre = self.nombre
            elif self.color != tapa_actual.color:
                tapa_actual.color = self.color
            elif self.descripcion != tapa_actual.descripcion:
                tapa_actual.descripcion = self.descripcion

        else:
            # Generar las nuevas abreviaturas del nombre y color
            
            nombre_abrev = self.descripcion[:3].capitalize()
            color_abrev = self.color.nombre[:3].capitalize()

            # Obtener el último consecutivo usado
            ultimo_consecutivo = Tapa.objects.filter( codigo__startswith=f"Tap{nombre_abrev}{color_abrev}").count()

            # Generar el nuevo consecutivo (3 dígitos)
            nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

            # Generar el código completo
            self.codigo = f"Tap{nombre_abrev}{color_abrev}{nuevo_consecutivo}"    

        super().save(*args, **kwargs) 
