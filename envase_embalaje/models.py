from django.db import models, transaction
from django.apps import apps
from bases.bases.models import ModeloBase
from .formato.models import Formato
from .tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from nomencladores.almacen.models import Almacen


class EnvaseEmbalaje(ModeloBase):
    codigo_envase = models.CharField(unique=True, null=False, blank=False, max_length=20, verbose_name="Código del envase")

    tipo_envase_embalaje = models.ForeignKey(TipoEnvaseEmbalaje, on_delete=models.DO_NOTHING, null=True, verbose_name="Tipo de envase de embalaje")

    formato = models.ForeignKey(Formato, on_delete=models.DO_NOTHING, null=True, verbose_name="Formato de envase")

    ESTADOS = [
        ('comprado', 'Comprado'),
        ('en_almacen', 'En almacén'),
        ('reservado', 'Reservado'),
    ]
    estado = models.CharField(choices=ESTADOS, max_length=255, blank=False, null=False, default='comprado', verbose_name='Estado')

    cantidad = models.IntegerField(null=True, default=0, verbose_name="Cantidad en almacen")

    costo = models.FloatField(null=True, blank=False, default=0, verbose_name="Costo")

    #almacen = models.ForeignKey(Almacen, on_delete=models.SET_NULL, null=True, verbose_name='Almacen')

    class Meta:
        verbose_name = "Envase o embalaje"
        verbose_name_plural = "Envases o embalajes"

    def __str__(self):
        return self.codigo_envase

    @property
    def all_almacenes(self):
        Almacen = apps.get_model('almacen', 'Almacen')
        return Almacen.objects.filter(envases=self)

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Verificar si el objeto ya existe en la base de datos
<<<<<<< Updated upstream
        print(self)
=======
       
>>>>>>> Stashed changes
        if self.pk:  # Si el objeto ya tiene un ID (ya existe)
            
            # Obtener el objeto actual desde la base de datos
            envase_actual = EnvaseEmbalaje.objects.filter(pk=self.pk).first

            if envase_actual:
                # Verificar si el material o el color han cambiado
                #if self.tipo_envase_embalaje!=envase_actual.tipo_envase_embalaje or self.formato!=envase_actual.formato:
                    # Extraer el consecutivo del código actual
                    consecutivo = self.codigo_envase[-3:]  # Los últimos 3 dígitos del código

                    # Generar las nuevas abreviaturas del material y color
                    tipo_envase_embalaje = self.tipo_envase_embalaje.codigo
                    unidad_medida = self.formato.unidad_medida

                    # Generar el nuevo código
                    self.codigo_envase = f"{tipo_envase_embalaje}{unidad_medida}{consecutivo}"
        else:
            # Si el objeto no existe, generar el código como antes
            if not self.codigo_envase:
                # Obtener el código del tipo de envase
                tipo_envase_codigo = self.tipo_envase_embalaje.codigo

                # Obtener la capacidad del formato
                capacidad = self.formato.unidad_medida

                # Obtener el último consecutivo usado
                ultimo_consecutivo = EnvaseEmbalaje.objects.filter(
                    codigo_envase__startswith=f"{tipo_envase_codigo}{capacidad}"
                ).count()

                # Generar el nuevo consecutivo (3 dígitos)
                nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

                # Generar el código completo
                self.codigo_envase = f"{tipo_envase_codigo}{capacidad}{nuevo_consecutivo}"

        # Guardar el objeto
        super().save(*args, **kwargs)
