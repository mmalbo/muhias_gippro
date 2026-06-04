# notifications/context_processors.py
from .models import Notification

def group_of(request):
    user = request.user
    almacenero = 'False'
    presidencia = 'False'
    admin = 'False'
    consultor = 'False'
    comercial = 'False'
    tecnologa = 'False'
    if user.groups.filter(name__in=['Almaceneros']):
        almacenero = 'True'
    if user.groups.filter(name__in=['Consultor']):
        consultor = 'True'
    if user.groups.filter(name__in=['Comercial']):
        comercial = 'True'
    if user.groups.filter(name__in=['Presidencia-Admin']):
        presidencia = 'True'
    if user.groups.filter(name__in=['Tecnologa']):
        tecnologa = 'True'
    if user.is_staff:
        admin = 'True'
    return {
        'almacenero': almacenero,
        'presidencia': presidencia,
        'admin': admin,
        'comercial': comercial,
        'consultor': consultor,
        'tecnologa':tecnologa
    }

def notifications(request):
    if request.user.is_authenticated:
        # Usar el modelo directamente para evitar problemas
        unread_count = Notification.objects.filter(
            user=request.user,
            read=False
        ).count()
        return {'unread_count': unread_count}
    return {'unread_count': 0}