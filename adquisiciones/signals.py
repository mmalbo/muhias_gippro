# products/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from utils.models import Notification
from .models import DetallesAdquisicion, DetallesAdquisicionEnvase, DetallesAdquisicionInsumo, Adquisicion
from utils.tasks import send_notification_email

@receiver(post_save, sender=Adquisicion)
def notify_adquisition_arrival(sender, instance, created, **kwargs):
    if created:  # Solo para nuevas adquisiciones
        # Obtener grupos objetivo
        target_groups = Group.objects.filter(name__in=["Almaceneros", "Presidencia-Admin"])
        # Crear notificaciones para cada usuario en esos grupos
        for group in target_groups:
            for user in group.customuser_set.all():
                # Notificación en base de datos
                Notification.objects.create(
                    user=user,
                    message=f"Nueva adquisición recibida: {instance}",
                    link=f'/movimientos/recepcion/{instance.tipo_adquisicion}/{instance.id}/'  # Ir a página para realizar la entrada al almacén.  
                )
                # Enviar email (asíncrono recomendado)
                #send_notification_email.delay(user.id, instance.id)  # Pasar IDs en lugar de objetos

""" @receiver(post_save, sender=DetallesAdquisicion)
def notify_mp_arrival(sender, instance, created, **kwargs):
    if created:  # Solo para nuevos productos
        # Obtener grupos objetivo
        target_groups = Group.objects.filter(name__in=["Almaceneros", "Presidencia-Admin"])
        
        # Crear notificaciones para cada usuario en esos grupos
        for group in target_groups:
            for user in group.customuser_set.all():
                # Notificación en base de datos
                Notification.objects.create(
                    user=user,
                    message=f"Nueva materia prima recibida: {instance.materia_prima}",
                    link=f"#"  # URL opcional
                )
                # Enviar email (asíncrono recomendado)
                #send_notification_email.delay(user.id, instance.id)  # Pasar IDs en lugar de objetos

@receiver(post_save, sender=DetallesAdquisicionEnvase)
def notify_envase_arrival(sender, instance, created, **kwargs):
    if created:  # Solo para nuevos productos
        # Obtener grupos objetivo
        target_groups = Group.objects.filter(name__in=["Almaceneros", "Presidencia-Admin"])
        
        # Crear notificaciones para cada usuario en esos grupos
        for group in target_groups:
            for user in group.customuser_set.all():
                # Notificación en base de datos
                Notification.objects.create(
                    user=user,
                    message=f"Nuevo envase o embalaje recibido: {instance.envase_embalaje}",
                    link=f"#"  # URL opcional
                )
                # Enviar email (asíncrono recomendado)
                #send_notification_email.delay(user.id, instance.id)  # Pasar IDs en lugar de objetos

@receiver(post_save, sender=DetallesAdquisicionInsumo)
def notify_insumo_arrival(sender, instance, created, **kwargs):
    if created:  # Solo para nuevos productos
        # Obtener grupos objetivo
        target_groups = Group.objects.filter(name__in=["Almaceneros", "Presidencia-Admin"])
        
        # Crear notificaciones para cada usuario en esos grupos
        for group in target_groups:
            for user in group.customuser_set.all():
                # Notificación en base de datos
                Notification.objects.create(
                    user=user,
                    message=f"Nuevo insumo recibido: {instance.insumo}",
                    link=f"#"  # URL opcional
                )
                # Enviar email (asíncrono recomendado)
                #send_notification_email.delay(user.id, instance.id)  # Pasar IDs en lugar de objetos
 """