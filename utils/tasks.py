from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_notification_email(user, product):
    subject = "Nuevo producto en almacén"
    message = f"Hola {user.username},\n\nSe ha recibido: \n\nSaludos!"
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )