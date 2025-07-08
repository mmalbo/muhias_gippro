import requests
from django.core.exceptions import ValidationError
from materia_prima.models import MateriaPrima


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

        for producto_data in productos_data:
            # Verificar si el producto ya existe por SKU
            materia_prima, created = MateriaPrima.objects.update_or_create(
                sku=producto_data['sku'],
                defaults={
                    'gname': producto_data.get('gname', ''),
                    'presentation': producto_data.get('presentation', ''),
                    'is_feedstock': producto_data.get('is_feedstock', False),
                    'count': producto_data.get('count', 0),
                    'categories': producto_data.get('categories', []),
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