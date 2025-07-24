import uuid

from django.db import models
from django.urls import reverse_lazy


class ModeloBase(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
      # editable=False,
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)

    def verbose_name(self):
        return self._meta.verbose_name

    def verbose_name_plural(self):
        return self._meta.verbose_name_plural

    def verbose_name_plural_limpio(self):
        return self._meta.verbose_name_plural.replace(" de ", "_").replace(" ", "_")

    def tabla_url(self):
        return reverse_lazy(f"{self.verbose_name_plural_limpio()}:filtro")

    def crud_simple(self):
        return True

    def creacion_url(self):
        return reverse_lazy(f"{self.verbose_name_plural_limpio()}:crear")

    def actualizacion_url(self):
        return reverse_lazy(
            f"{self.verbose_name_plural_limpio()}:actualizar", kwargs={"pk": self.pk}
        )

    def detalle_url(self):
        return reverse_lazy(
            f"{self.verbose_name_plural_limpio()}:detalle", kwargs={"pk": self.pk}
        )

    def get_absolute_url(self):
        return self.detalle_url()

    def obtener_fields_values(self):
        return [
            (field.verbose_name, getattr(self, field.name))
            for field in self._meta.fields
            if field.name
               not in [
                   "id",
                   "fecha_creacion",
                   "fecha_actualizacion",
               ]
        ]

    def acciones(self):
        return [
            {
                "categoria": "acciones",
                "acciones": [
                    {
                        "label": f"actualizar {self.verbose_name()}",
                        "url": self.actualizacion_url(),
                    },
                ],
            },
            {
                "categoria": "visualizaciones",
                "acciones": [
                    {
                        "label": f"visualizar listado de {self.verbose_name_plural()}",
                        "url": self.tabla_url(),
                    },
                ],
            },
        ]

    @staticmethod
    def exclude_fields():
        excluded_fields_table = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        excluded_fields_filter = excluded_fields_table + []
        return {
            "table": excluded_fields_table,
            "filter": excluded_fields_filter,
        }
