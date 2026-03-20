from django.db import models, transaction
from bases.bases.models import ModeloBase
from django.db.models import Sum
from nomencladores.almacen.models import Almacen


# Create your models here.

class InsumosOtros(ModeloBase):
    codigo = models.CharField(
        verbose_name="Código de insumo",
        unique=True,
        null=False, max_length=20
    )

    ESTADOS = [
        ('comprado', 'Comprado'),
        ('en_almacen', 'En almacén'),
        ('reservado', 'Reservado'),
    ]
    estado = models.CharField(
        choices=ESTADOS,
        max_length=255,
        null=False,
        verbose_name='Estado'
    )

    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre",
        null=False, blank=False,
    )

    descripcion = models.CharField(
        max_length=600,
        verbose_name="Descripción",
        null=False, blank=False,
    )

    costo = models.FloatField(
        null=True,
        blank=False,
        default=0,
        verbose_name="Costo",
    )

    @property
    def cantidad_total(self):
        """
        Calcula la cantidad total de este envase en todos los almacenes
        """
        total = self.inventarios_ins.aggregate(
            total=Sum('cantidad')
        )['total']
        return total if total is not None else 0
    
    def __str__(self):
        return self.nombre

    @transaction.atomic
    def save(self, *args, **kwargs):
        print("En el save")
        if self.pk:  # Si el objeto ya tiene un ID (ya existe)
            print("Ya existe")
            insumo_actual = InsumosOtros.objects.filter(pk=self.pk).first

            if insumo_actual:
                print("Insumo actual")
                consecutivo = self.codigo[-3:]  # Los últimos 3 dígitos del código
                print(consecutivo)
                if not consecutivo:
                    consecutivo = '001'
                print(consecutivo)
                # Generar las nuevas abreviaturas del material y color
                nombre = self.nombre

                # Generar el nuevo código
                self.codigo = f"{nombre}{consecutivo}"
                print(f"{self.codigo}")
            else:
                print("No encontro el insumo")
        else:
            print("No existe")
            # Si el objeto no existe, generar el código como antes
            if not self.codigo:
                print("No tiene codigo")
                # Obtener el código del tipo de envase
                codigo = self.nombre

                # Obtener el último consecutivo usado
                ultimo_consecutivo = InsumosOtros.objects.filter(
                    codigo__startswith=f"{codigo}"
                ).count()

                # Generar el nuevo consecutivo (3 dígitos)
                nuevo_consecutivo = f"{ultimo_consecutivo + 1:03d}"

                # Generar el código completo
                self.codigo = f"{codigo}{nuevo_consecutivo}"
                print(self.codigo)
            else:
                print("Ya tiene código y no hago nada")

        # Guardar el objeto
        print("A guardar super")
        try:
            super().save(*args, **kwargs)
            print("Paso el super save")
        except Exception as e:
            print(f"{e}")

