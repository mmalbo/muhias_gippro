# notifications/context_processors.py
from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        # Usar el modelo directamente para evitar problemas
        unread_count = Notification.objects.filter(
            user=request.user,
            read=False
        ).count()
        return {'unread_count': unread_count}
    return {'unread_count': 0}