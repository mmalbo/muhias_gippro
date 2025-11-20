import requests
from django.core.exceptions import ValidationError
from materia_prima.models import MateriaPrima
from producto.models import Producto 
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.csrf import csrf_exempt
from nomencladores.models import Almacen
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_MP, Movimiento_Prod
from inventario.models import Inv_Mat_Prima, Inv_Producto
from envase_embalaje.models import Formato 

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
        contador_nuevos = 1

        almacen = Almacen.objects.first() 
        print(almacen)

        for producto_data in productos_data:
            # Verificar si el producto ya existe por SKU
            is_feedstock = producto_data.get('is_feedstock', False)
            #print(producto_data.get('sku', ''))
            created = False
            codigon = producto_data.get('sku', '')
            print(producto_data)
            categorias = producto_data.get('categories', '')
            categoria = categorias[0].get('name', '')
            print(categoria)
            if is_feedstock:
                materia_prima, created_mp = MateriaPrima.objects.update_or_create(                    
                    nombre=producto_data.get('gname', ''),
                    defaults={
                    'unidad_medida': producto_data.get('presentation', ''),
                    'tipo_materia_prima' : categoria.lower(),
                    }
                )
                
                materia_prima.save()
                
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
                    print(contador_nuevas)
                else:
                    print("No se creo nueva")
                codigon = ''
            else:
                cant_vieja = 0
                formato_str = producto_data.get('presentation', '').lower()
                cap_str = ''
                print(formato_str)
                for i in formato_str:
                    try:
                        if int(i) or i == '0':
                            print(i)
                            cap_str = cap_str + i
                        else:
                            print('else')
                            break
                    except:
                        print('except')
                        break
                if cap_str == '':
                    capacidad = 0
                else:
                    capacidad = int(cap_str)
                    print(cap_str)
                    print(capacidad)
                if 'kg' in formato_str:
                    um = 'Kg'
                    print('kg en cadena formato')
                elif 'ml' in formato_str:
                    um = 'ml'
                elif 'granel' in formato_str:
                    capacidad = 0
                    um = 'L'
                else:
                    um = 'L'
                print(f'um: {um}, cap: {capacidad}')
                formato = Formato.objects.filter(unidad_medida=um, capacidad=capacidad).first()
                if not formato:
                    print('No encontro formato')
                    formato = Formato.objects.create(unidad_medida=um, capacidad=capacidad)
                else:
                    print('Ya encontro formato')
                nomb_prod = producto_data.get('gname', '')
                print(nomb_prod)
                producto = Producto.objects.filter(                    
                    nombre_comercial= nomb_prod, formato = formato
                ).first()
                if not producto:
                    print('no hay producto')
                    try:
                        producto = Producto.objects.create(nombre_comercial = nomb_prod, formato = formato, costo=0.00)
                        created_prod = True
                    except Exception as e:
                        print(f"Error al crear nuevo producto: {str(e)}")
                        continue
                else:
                    print('encontro producto')
                    producto.formato = formato
                    created_prod = False
                    cant_vieja = producto.count
                vale = Vale_Movimiento_Almacen.objects.create(
                    almacen = almacen,
                    entrada = True
                )
                print('Creado el vale')
                cantidad = decimal.Decimal(producto_data.get('count', '0'))
                print(f'Cantidad: {cantidad}')
                if cantidad != 0:
                    try:
                        mov = Movimiento_Prod.objects.create(
                            producto=producto,
                            vale_e=vale,  # Ejemplo: atributo fijo
                            cantidad=cantidad                        
                        )
                        if mov:
                            print('existe Movimiento_Prod')
                        else:
                            print('Eres comemierda')
                        print('creado movimiento')
                        inventario_prod, created_inv = Inv_Producto.objects.get_or_create(
                            producto=producto, almacen=almacen)
                        if created_inv:
                            print('Creado inventario')
                            print(inventario_prod.almacen)
                        else:
                            print('No fue ceado el inventario')
                            print(inventario_prod.almacen)
                        if cantidad > inventario_prod.cantidad:
                            vale.entrada = True 
                            mov.cantidad = cantidad - inventario_prod.cantidad
                        else:
                            vale.entrada = False
                            mov.cantidad = inventario_prod.cantidad - cantidad
                        vale.save()
                        mov.save()
                        inventario_prod.cantidad = cantidad
                        inventario_prod.save()
                        print('Guardado inventario')
                    except Exception as e: #(ValueError, TypeError):
                        print(f"Error...{e}")
                        pass
                else:
                    print("No encontro cantidad")
                if created_prod:
                    contador_nuevos += 1
                    print(contador_nuevos)
                else:
                    print("No se creo nueva")
                codigon = ''
        print(f'status: success, message: Se importaron {contador_nuevos} productos nuevos. Total procesados: {len(productos_data)}')

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