from django.db import models, transaction
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from django.core.exceptions import ValidationError


def validate_material(value):
    """
    Valida que el material tenga al menos 3 caracteres.
    """
    if len(value) < 3:
        raise ValidationError("El material debe tener al menos 3 caracteres.")

def validate_tamanno(value):
    """
    Valida que el tamaño tenga al menos 2 caracteres.
    """
    if len(value) < 2:
        raise ValidationError("El tamaño debe tener al menos 2 caracteres.")

class Caja(TipoEnvaseEmbalaje):
    """ nombre = models.CharField(
        max_length=255,
        blank=False, null=False,
        verbose_name="Nombre"
    ) """
    tamanno = models.CharField(
        max_length=255,
        blank=False, null=False,
        validators=[validate_tamanno],
        verbose_name="Tamaño"
    )
    material = models.CharField(
        max_length=255,
        blank=False, null=False,
        validators=[validate_material],
        verbose_name="Material"
    )

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Verificar si el objeto ya existe en la base de datos
        if self.pk:  # Si el objeto ya tiene un ID (ya existe)
            # Obtener el objeto actual desde la base de datos
            caja_actual = Caja.objects.get(pk=self.pk)

            # Verificar si el material o el tamaño han cambiado
            if self.material != caja_actual.material or self.tamanno != caja_actual.tamanno:
                # Extraer el consecutivo del código actual
                consecutivo = self.codigo[-3:]  # Los últimos 3 dígitos del código

                # Generar las nuevas abreviaturas del material y tamaño
                material_abrev = self.material[:3].capitalize()
                tamanno_abrev = self.tamanno[:2].capitalize()

                # Generar el nuevo código
                self.codigo = f"C{material_abrev}{tamanno_abrev}{consecutivo}"
        else:
            # Si el objeto no existe, generar el código como antes
            if not self.codigo:
                material_abrev = self.material[:3].capitalize()
                tamanno_abrev = self.tamanno[:2].capitalize()

                # Obtener el último consecutivo usado
                ultimo_consecutivo = Caja.objects.filter(
                    codigo__startswith=f"C{material_abrev}{tamanno_abrev}"
                ).count()

                # Generar el nuevo consecutivo (3 dígitos)
                nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

                # Generar el código completo
                self.codigo = f"C{material_abrev}{tamanno_abrev}{nuevo_consecutivo}"

        super().save(*args, **kwargs)