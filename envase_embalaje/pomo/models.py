from django.db import models, transaction
from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from django.core.exceptions import ValidationError


def validate_material(value):
    """
    Valida que el material tenga al menos 3 caracteres.
    """
    if len(value) < 3:
        raise ValidationError("El material debe tener al menos 3 caracteres.")

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

class Pomo(TipoEnvaseEmbalaje):
    """ nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre"
    ) """
    color = models.ForeignKey(
        Color,
        on_delete=models.DO_NOTHING,
        verbose_name="Color",
        validators=[validate_color]  # Aplicar la validación aquí
    )
    forma = models.CharField(
        max_length=255,
        verbose_name="Forma"
    )
    material = models.CharField(
        max_length=255,
        verbose_name="Material",
        validators=[validate_material]  # Aplicar la validación aquí
    )

    class Meta:
        verbose_name = "Pomo"
        verbose_name_plural = "Pomos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Verificar si el objeto ya existe en la base de datos
        if self.pk:  # Si el objeto ya tiene un ID (ya existe)
            # Obtener el objeto actual desde la base de datos
            pomo_actual = Pomo.objects.get(pk=self.pk)

            # Verificar si el material o el color han cambiado
            if self.material != pomo_actual.material or self.color != pomo_actual.color:
                # Extraer el consecutivo del código actual
                consecutivo = self.codigo[-3:]  # Los últimos 3 dígitos del código

                # Generar las nuevas abreviaturas del material y color
                material_abrev = self.material[:3].capitalize()
                color_abrev = self.color.nombre[:3].capitalize()

                # Generar el nuevo código
                self.codigo = f"P{material_abrev}{color_abrev}{consecutivo}"
        else:
            # Si el objeto no existe, generar el código como antes
            if not self.codigo:
                material_abrev = self.material[:3].capitalize()
                color_abrev = self.color.nombre[:3].capitalize()

                # Obtener el último consecutivo usado
                ultimo_consecutivo = Pomo.objects.filter(
                    codigo__startswith=f"P{material_abrev}{color_abrev}"
                ).count()

                # Generar el nuevo consecutivo (3 dígitos)
                nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

                # Generar el código completo
                self.codigo = f"P{material_abrev}{color_abrev}{nuevo_consecutivo}"

        super().save(*args, **kwargs)