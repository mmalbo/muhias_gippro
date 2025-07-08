from django.db import models, transaction
from nomencladores.color.models import Color
from envase_embalaje.tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from django.core.exceptions import ValidationError


def validate_material(value):
    if len(value) < 3:
        raise ValidationError("El material debe tener al menos 3 caracteres.")

def validate_color(value):
    try:
        color_instance = Color.objects.get(id=value)
    except Color.DoesNotExist:
        raise ValidationError("El color seleccionado no existe.")

    if len(color_instance.nombre) < 3:
        raise ValidationError("El nombre del color debe tener al menos 3 caracteres.")


class Tanque(TipoEnvaseEmbalaje):
    #nombre = models.CharField(max_length=255, verbose_name="Nombre")
    color = models.ForeignKey(Color, on_delete=models.DO_NOTHING, verbose_name="Color", validators=[validate_color])
    material = models.CharField(max_length=255, verbose_name="Material", validators=[validate_material])

    class Meta:
        verbose_name = "Tanque"
        verbose_name_plural = "Tanques"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk:  # Si el objeto ya existe
            tanque_actual = Tanque.objects.get(pk=self.pk)
            if self.material != tanque_actual.material or self.color != tanque_actual.color:
                consecutivo = self.codigo[-3:]  # Extraer el consecutivo
                material_abrev = self.material[:3].capitalize()
                color_abrev = self.color.nombre[:3].capitalize()
                self.codigo = f"T{material_abrev}{color_abrev}{consecutivo}"
        else:  # Si el objeto no existe
            if not self.codigo:
                material_abrev = self.material[:3].capitalize()
                color_abrev = self.color.nombre[:3].capitalize()
                ultimo_consecutivo = Tanque.objects.filter(codigo__startswith=f"T{material_abrev}{color_abrev}").count()
                nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"
                self.codigo = f"T{material_abrev}{color_abrev}{nuevo_consecutivo}"

        super().save(*args, **kwargs)
