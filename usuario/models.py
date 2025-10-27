from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Cambia el nombre del acceso inverso para 'groups'
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Cambia el nombre del acceso inverso para 'user_permissions'
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
        related_query_name='customuser',  # Cambia el nombre del acceso inverso para consultas
    )

    class Meta:
        permissions = (
            ("can_administracion", "Administración"),
            ("can_clasificadores", "Clasificadores"),
            ("can_inventario", "Inventario"),
            ("can_adquisiciones", "Adquisiciones"),
            ("can_envasado", "Envasado"),
            ("can_produccion", "Producción"),
        )

    @property
    def of_group(self, group_name):
        return self.groups.filter(name = group_name).exists()
