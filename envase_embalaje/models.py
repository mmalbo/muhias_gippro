from django.db import models, transaction
from django.apps import apps
from bases.bases.models import ModeloBase
from .formato.models import Formato
from .tipo_envase_embalaje.models import TipoEnvaseEmbalaje
from nomencladores.almacen.models import Almacen
from django.db.models import Sum


class EnvaseEmbalaje(ModeloBase):
    codigo_envase = models.CharField(unique=True, null=False, blank=False, max_length=20, verbose_name="Código del envase")
    nombre = models.CharField(max_length=255, verbose_name="Nombre",blank=False, null=False, default="Envase")
    tipo_envase_embalaje = models.ForeignKey(TipoEnvaseEmbalaje, on_delete=models.DO_NOTHING, null=True, verbose_name="Tipo de envase de embalaje")
    formato = models.ForeignKey(Formato, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Formato de envase")
    proveedor = models.CharField(max_length=255, verbose_name="Proveedor",blank=False, null=False, default="Proveedor")

    ESTADOS = [
        ('comprado', 'Comprado'),
        ('en_almacen', 'En almacén'),
        ('reservado', 'Reservado'),
    ]
    estado = models.CharField(choices=ESTADOS, max_length=255, blank=False, null=False, default='comprado', verbose_name='Estado')

    costo = models.FloatField(null=True, blank=False, default=0, verbose_name="Costo")

    #almacen = models.ForeignKey(Almacen, on_delete=models.SET_NULL, null=True, verbose_name='Almacen')

    class Meta:
        verbose_name = "Envase o embalaje"
        verbose_name_plural = "Envases o embalajes"

    def __str__(self):
        if self.formato:
            return self.tipo_envase_embalaje.nombre + ' ' + str(self.formato.capacidad) + ' ' + self.formato.unidad_medida 
        else:
            return self.tipo_envase_embalaje.nombre

    @property
    def cantidad_total(self):
        """
        Calcula la cantidad total de este envase en todos los almacenes
        """
        total = self.inventarios_env.aggregate(
            total=Sum('cantidad')
        )['total']
        return total if total is not None else 0 
    
    @property
    def all_almacenes(self):
        Almacen = apps.get_model('almacen', 'Almacen')
        return Almacen.objects.filter(envases=self)

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Verificar si el objeto ya existe en la base de datos
       
        if self.pk:  # Si el objeto ya tiene un ID (ya existe)
            print("Existe un envase " + self.codigo_envase)
            # Obtener el objeto actual desde la base de datos
            envase_actual = EnvaseEmbalaje.objects.filter(pk=self.pk).first
            print(envase_actual)

            if not self.codigo_envase:
                # Generar las nuevas abreviaturas del material y color
                tipo_envase_codigo = self.tipo_envase_embalaje.codigo
                print("Codigo del tipo envase: "+self.tipo_envase_embalaje.codigo)
                proveedor = self.proveedor[:3].capitalize()

                # Obtener el último consecutivo usado
                ultimo_consecutivo = EnvaseEmbalaje.objects.filter( 
                                    codigo_envase__startswith=f"{tipo_envase_codigo}{proveedor}" 
                                    ).count()
                
                print("==========")
                print(ultimo_consecutivo)
                nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

                """if ultimo_consecutivo == 1:
                    nuevo_consecutivo = self.codigo_envase[-3:]
                else:
                    "
                print("==========")
                print(nuevo_consecutivo)
                # Extraer el consecutivo del código actual
                #consecutivo = self.codigo_envase[-3:]  # Los últimos 3 dígitos del código
                """
                # Generar el nuevo código
                self.codigo_envase = f"{tipo_envase_codigo}{proveedor}{nuevo_consecutivo}"
                print("==========")
                print(self.codigo_envase)
                """else:
                # Si el objeto no existe, generar el código como antes
                if not self.codigo_envase:
                    # Obtener el código del tipo de envase
                    tipo_envase_codigo = self.tipo_envase_embalaje.codigo

                    # Obtener el proveedor
                    proveedor = self.proveedor[:3].capitalize()

                    # Obtener el último consecutivo usado
                    ultimo_consecutivo = EnvaseEmbalaje.objects.filter(
                        codigo_envase__startswith=f"{tipo_envase_codigo}{proveedor}"
                        ).count()

                    # Generar el nuevo consecutivo (3 dígitos)
                    nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

                    # Generar el código completo
                    self.codigo_envase = f"{tipo_envase_codigo}{proveedor}{nuevo_consecutivo}"
                    print(f"Nuevo: {self.codigo_envase}")"""

        # Guardar el objeto
        super().save(*args, **kwargs)
