from django.db import models
from usuario.models import CustomUser

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notification')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Campos adicionales (opcional)
    link = models.URLField(blank=True, null=True) 

    def __str__(self):
        return self.message

"""
# models.py
from django.db import models
import uuid
from django.contrib.auth.models import User

class Notificacion(models.Model):
    TIPOS_NOTIFICACION = [
        ('produccion_creada', 'Producción Creada'),
        ('produccion_iniciada', 'Producción Iniciada'),
        ('produccion_completada', 'Producción Completada'),
        ('produccion_cancelada', 'Producción Cancelada'),
        ('pruebas_subidas', 'Pruebas Químicas Subidas'),
        ('inventario_actualizado', 'Inventario Actualizado'),
    ]
    
    NIVELES = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('success', 'Éxito'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=50, choices=TIPOS_NOTIFICACION)
    nivel = models.CharField(max_length=20, choices=NIVELES, default='info')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    relacion_contenido_type = models.ForeignKey(
        'contenttypes.ContentType', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    relacion_contenido_id = models.UUIDField(null=True, blank=True)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
    
    def marcar_como_leida(self):
        self.leida = True
        self.save()
    
    @property
    def relacion_contenido(self):
        if self.relacion_contenido_type and self.relacion_contenido_id:
            return self.relacion_contenido_type.get_object_for_this_type(id=self.relacion_contenido_id)
        return None
"""