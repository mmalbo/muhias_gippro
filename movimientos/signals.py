from django.db.models.signals import post_save
from django.dispatch import receiver
from utils.models import Notification
from .models import Vale_Movimiento_Almacen
from utils.tasks import send_notification_email

