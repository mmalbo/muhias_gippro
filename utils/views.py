import requests
from django.core.exceptions import ValidationError
from materia_prima.models import MateriaPrima
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.csrf import csrf_exempt

def importar_productos_desde_api():
    url = "http://testtienda.produccionesmuhia.ca/catalogo/listarGippro/"
    params = {
        'fields': 'gname,presentation,sku,is_feedstock,count,categories'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lanza excepción para errores HTTP

        productos_data = response.json()
        contador = 0

        print(productos_data)

        for producto_data in productos_data:
            # Verificar si el producto ya existe por SKU
            is_feedstock = producto_data.get('is_feedstock', False)
            print(producto_data.get('sku', ''))
            created = False
            if is_feedstock:
                materia_prima, created = MateriaPrima.objects.update_or_create(
                    codigo=producto_data.get('sku', ''),
                    defaults={
                    'nombre': producto_data.get('gname', ''),
                    'unidad_medida': producto_data.get('presentation', ''),
                }
            )

            if created:
                contador += 1

        return {
            'status': 'success',
            'message': f'Se importaron {contador} productos nuevos. Total procesados: {len(productos_data)}'
        }

    except requests.exceptions.RequestException as e:
        raise ValidationError(f"Error al conectar con la API: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error inesperado: {str(e)}")
    
    # notifications/views.py


@login_required
def unread_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user, 
        read=False
    ).order_by('-created_at').values('id', 'message', 'created_at', 'link')[:20]
    
    # Formatear fecha
    for notif in notifications:
        notif['created_at'] = notif['created_at'].strftime("%d/%m/%Y %H:%M")
    
    return JsonResponse(list(notifications), safe=False)

@login_required
@csrf_exempt
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.read = True
        notification.save()
        return JsonResponse({"status": "success"})
    except Notification.DoesNotExist:
        return JsonResponse({"status": "error"}, status=404)

@login_required
@csrf_exempt
def mark_all_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return JsonResponse({"status": "success"})