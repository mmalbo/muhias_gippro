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
