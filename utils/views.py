import requests
from django.core.exceptions import ValidationError
from materia_prima.models import MateriaPrima
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.csrf import csrf_exempt
from nomencladores.models import Almacen
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_MP
from inventario.models import Inv_Mat_Prima
import decimal

def importar_productos_desde_api(request):
    url = "http://testtienda.produccionesmuhia.ca/catalogo/listarGippro/"
    params = {
        'fields': 'gname,presentation,sku,is_feedstock,count,categories'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lanza excepción para errores HTTP

        productos_data = response.json()
        contador_nuevas = 1

        almacen = Almacen.objects.first() 
        print(almacen)

        for producto_data in productos_data:
            # Verificar si el producto ya existe por SKU
            is_feedstock = producto_data.get('is_feedstock', False)
            #print(producto_data.get('sku', ''))
            created = False
            codigon = producto_data.get('sku', '')
            if is_feedstock:
                materia_prima, created_mp = MateriaPrima.objects.update_or_create(                    
                    nombre=producto_data.get('gname', ''),
                    defaults={
                    'unidad_medida': producto_data.get('presentation', ''),
                    }
                )
                if created_mp:
                    print(materia_prima.codigo)
                else:
                    print('Existe la materia prima')
                vale = Vale_Movimiento_Almacen.objects.create(
                    almacen = almacen,
                    entrada = True
                )
                print('Creado el vale')
                cantidad = decimal.Decimal(producto_data.get('count', '0'))
                print(f'Cantidad: {cantidad}')
                if cantidad != 0:
                    try:
                        mov = Movimiento_MP.objects.create(
                            materia_prima=materia_prima,
                            vale=vale,  # Ejemplo: atributo fijo
                            cantidad=cantidad                        
                        )
                        if mov:
                            print('existe Movimiento_MP')
                        else:
                            print('Eres comemierda')
                        print('creado movimiento')
                        inventario_mp, created_inv = Inv_Mat_Prima.objects.get_or_create(
                            materia_prima=materia_prima, almacen=almacen)
                        if created_inv:
                            print('Creado inventario')
                            print(inventario_mp.almacen)
                        else:
                            print('No fue ceado el inventario')
                            print(inventario_mp.almacen)
                        if cantidad > inventario_mp.cantidad:
                            vale.entrada = True 
                            mov.cantidad = cantidad - inventario_mp.cantidad
                        else:
                            vale.entrada = False
                            mov.cantidad = inventario_mp.cantidad - cantidad
                        vale.save()
                        mov.save()
                        inventario_mp.cantidad = cantidad
                        inventario_mp.save()
                        print('Guardado inventario')
                    except Exception as e: #(ValueError, TypeError):
                        print(f"Error...{e}")
                        pass
                else:
                    print("No encontro cantidad")
                if created_mp:
                    contador_nuevas += 1
                codigon = ''
        return {
            'status': 'success',
            'message': f'Se importaron {contador_nuevas} productos nuevos. Total procesados: {len(productos_data)}'
        }
    except requests.exceptions.RequestException as e:
        raise ValidationError(f"Error al conectar con la API: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error inesperado: {e}")
    
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