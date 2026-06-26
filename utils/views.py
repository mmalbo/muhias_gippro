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
from django.contrib import messages
from django.shortcuts import redirect, render
from datetime import date, datetime, timezone
import json
# dashboard/views.py
from decimal import Decimal
from django.db.models import Count, Sum, Q, F, DecimalField, OuterRef, Subquery, Value, IntegerField
from django.db.models.functions import Coalesce

# Importaciones de tus modelos
from adquisiciones.models import Adquisicion
from movimientos.models import Vale_Movimiento_Almacen, Movimiento_EE, Movimiento_Ins, Movimiento_MP, Movimiento_Prod
from inventario.models import (
    Inv_Mat_Prima, Inv_Producto, Inv_Envase, Inv_Insumos
)
from produccion.models import Produccion
from producto.models import Producto
from envase_embalaje.models import EnvaseEmbalaje
from InsumosOtros.models import InsumosOtros
from materia_prima.models import MateriaPrima

# Funciones auxiliares

def obtener_desglose_por_tipo_inventario(modelo_movimiento, campo_inv, campo_nombre, fecha_inicio=None, fecha_fin=None, es_salida=True):
    """
    Devuelve un diccionario con el desglose por tipo de inventario para movimientos pendientes.
    modelo_movimiento: Movimiento_MP, Movimiento_Prod, etc.
    campo_inv: el campo que referencia al inventario (ej. 'materia_prima' para MP, 'producto' para Prod, etc.)
    campo_nombre: el campo del modelo de inventario que contiene el nombre del ítem.
    fecha_inicio/fecha_fin: para filtrar por fecha (opcional)
    es_salida: True para salidas, False para entradas (pero aquí usamos el estado del vale)
    """
    # Obtener los movimientos que cumplen el filtro de fecha (si se da) y que están pendientes (estado borrador o confirmado)
    # y que correspondan a salidas (entrada=False) o entradas (entrada=True) según es_salida.
    movs = modelo_movimiento.objects.filter(
        vale__estado__in=['borrador', 'confirmado'],
        vale__entrada = not es_salida  # si es salida, entrada=False; si es entrada, entrada=True
    )
    if fecha_inicio and fecha_fin:
        movs = movs.filter(vale__fecha_movimiento__range=[fecha_inicio, fecha_fin])
    
    # Agrupar por tipo de inventario (usamos el campo 'tipo' del inventario, que existe en ItemInventarioBase)
    # Pero necesitamos mapear cada movimiento a su tipo. Podemos hacerlo por separado.
    # Como son modelos diferentes, hacemos consultas separadas para cada tipo.
    # Construimos un diccionario con totales por tipo.
    tipos = ['materia_prima', 'producto', 'envase', 'insumo']
    desglose = {t: {'total': 0, 'items': []} for t in tipos}
    
    # Para cada tipo, filtramos el modelo de movimiento correspondiente y sumamos cantidades.
    # Usamos el modelo de inventario para obtener el nombre.
    # Nota: Asumimos que el campo cantidad en los movimientos es 'cantidad'.
    if modelo_movimiento == Movimiento_MP:
        qs = modelo_movimiento.objects.filter(vale__estado__in=['borrador', 'confirmado'], vale__entrada=not es_salida)
        if fecha_inicio and fecha_fin:
            qs = qs.filter(vale__fecha_movimiento__range=[fecha_inicio, fecha_fin])
        # Agrupar por materia_prima (Inv_Mat_Prima) y sumar cantidad
        items = qs.values('materia_prima_id', 'materia_prima__materia_prima__nombre').annotate(total=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))).order_by('-total')
        for item in items:
            desglose['materia_prima']['total'] += item['total'] or 0
            desglose['materia_prima']['items'].append({
                'nombre': item['materia_prima__materia_prima__nombre'],
                'cantidad': item['total']
            })
    elif modelo_movimiento == Movimiento_Prod:
        qs = modelo_movimiento.objects.filter(vale__estado__in=['borrador', 'confirmado'], vale__entrada=not es_salida)
        if fecha_inicio and fecha_fin:
            qs = qs.filter(vale__fecha_movimiento__range=[fecha_inicio, fecha_fin])
        items = qs.values('producto_id', 'producto__producto__nombre_comercial').annotate(total=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))).order_by('-total')
        for item in items:
            desglose['producto']['total'] += item['total'] or 0
            desglose['producto']['items'].append({
                'nombre': item['producto__producto__nombre_comercial'],
                'cantidad': item['total']
            })
    elif modelo_movimiento == Movimiento_EE:
        qs = modelo_movimiento.objects.filter(vale__estado__in=['borrador', 'confirmado'], vale__entrada=not es_salida)
        if fecha_inicio and fecha_fin:
            qs = qs.filter(vale__fecha_movimiento__range=[fecha_inicio, fecha_fin])
        items = qs.values('envase_embalaje_id', 'envase_embalaje__codigo_envase').annotate(total=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))).order_by('-total')
        for item in items:
            desglose['envase']['total'] += item['total'] or 0
            desglose['envase']['items'].append({
                'nombre': item['envase_embalaje__codigo_envase'],
                'cantidad': item['total']
            })
    elif modelo_movimiento == Movimiento_Ins:
        qs = modelo_movimiento.objects.filter(vale__estado__in=['borrador', 'confirmado'], vale__entrada=not es_salida)
        if fecha_inicio and fecha_fin:
            qs = qs.filter(vale__fecha_movimiento__range=[fecha_inicio, fecha_fin])
        items = qs.values('insumo_id', 'insumo__nombre').annotate(total=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))).order_by('-total')
        for item in items:
            desglose['insumo']['total'] += item['total'] or 0
            desglose['insumo']['items'].append({
                'nombre': item['insumo__nombre'],
                'cantidad': item['total']
            })
    else:
        raise ValueError("Modelo de movimiento no soportado")
    
    return desglose

def obtener_lento_movimiento(fecha_inicio, fecha_fin):
    """
    Retorna un diccionario con los elementos que NO han tenido movimiento (ni entrada ni salida)
    en el período [fecha_inicio, fecha_fin] (consideramos desde el primer día del mes anterior hasta hoy).
    Devuelve desglose por tipo.
    """
    # Obtener IDs de elementos que sí tuvieron movimiento en el período
    # Para cada tipo de inventario, obtener IDs de los movimientos (entrada o salida) en el período
    tipos = ['materia_prima', 'producto', 'envase', 'insumo']
    resultado = {t: {'total': 0, 'formato': '', 'items': []} for t in tipos}
    
    # 1. Materias primas: obtener IDs de Inv_Mat_Prima que aparecen en Movimiento_MP (entrada o salida) en el período
    ids_con_movimiento = Movimiento_MP.objects.filter(
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values_list('materia_prima_id', flat=True).distinct()
    # Todos los Inv_Mat_Prima
    todos_mp = Inv_Mat_Prima.objects.all().values('id', 'materia_prima__nombre')
    sin_mov = [mp for mp in todos_mp if mp['id'] not in ids_con_movimiento]
    resultado['materia_prima']['total'] = len(sin_mov)
    resultado['materia_prima']['items'] = [{'nombre': mp['materia_prima__nombre'], 'cantidad': 0} for mp in sin_mov]  # cantidad 0 (sin movimiento)
    
    # 2. Productos
    """ ids_con_movimiento = Movimiento_Prod.objects.filter(
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values_list('producto_id', flat=True).distinct()
    todos_prod = Inv_Producto.objects.all().values('id', 'producto__nombre_comercial', 'formato')
    sin_mov = [p for p in todos_prod if p['id'] not in ids_con_movimiento]
    resultado['producto']['formato']['total'] = len(sin_mov)
    resultado['producto']['formato']['items'] = [{'nombre': p['producto__nombre_comercial'], 'formato':p['formato'], 'cantidad': 0} for p in sin_mov]
     """
    # 3. Envases
    ids_con_movimiento = Movimiento_EE.objects.filter(
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values_list('envase_embalaje_id', flat=True).distinct()
    todos_env = Inv_Envase.objects.all().values('id', 'envase__codigo_envase')
    sin_mov = [e for e in todos_env if e['id'] not in ids_con_movimiento]
    resultado['envase']['total'] = len(sin_mov)
    resultado['envase']['items'] = [{'nombre': e['envase__codigo_envase'], 'cantidad': 0} for e in sin_mov]
    
    # 4. Insumos
    ids_con_movimiento = Movimiento_Ins.objects.filter(
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values_list('insumo_id', flat=True).distinct()
    todos_ins = Inv_Insumos.objects.all().values('id', 'insumos__nombre')
    sin_mov = [i for i in todos_ins if i['id'] not in ids_con_movimiento]
    resultado['insumo']['total'] = len(sin_mov)
    resultado['insumo']['items'] = [{'nombre': i['insumos__nombre'], 'cantidad': 0} for i in sin_mov]
    
    return resultado

def obtener_bajo_inventario(fecha_inicio, fecha_fin):
    """
    Elementos cuyo stock actual es menor que la cantidad total de salidas en el período.
    """
    # Stock actual por tipo de inventario
    tipos = ['materia_prima', 'producto', 'envase', 'insumo']
    resultado = {t: {'total': 0, 'items': []} for t in tipos}
    
    # Para cada tipo, obtener stock total y salidas totales
    # Materia prima
    stock_mp = Inv_Mat_Prima.objects.values('id', 'materia_prima__nombre', 'cantidad')
    salidas_mp = Movimiento_MP.objects.filter(
        vale__entrada=False,
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values('materia_prima_id').annotate(total_salidas=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))
    salidas_dict = {item['materia_prima_id']: item['total_salidas'] for item in salidas_mp}
    for mp in stock_mp:
        salidas = salidas_dict.get(mp['id'], Decimal('0'))
        if mp['cantidad'] < salidas:
            resultado['materia_prima']['total'] += 1
            resultado['materia_prima']['items'].append({
                'nombre': mp['materia_prima__nombre'],
                'stock': mp['cantidad'],
                'salidas': salidas
            })
    
    # Productos
    stock_prod = Inv_Producto.objects.values('id', 'producto__nombre_comercial', 'cantidad')
    salidas_prod = Movimiento_Prod.objects.filter(
        vale__entrada=False,
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values('producto_id').annotate(total_salidas=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))
    salidas_dict = {item['producto_id']: item['total_salidas'] for item in salidas_prod}
    for p in stock_prod:
        salidas = salidas_dict.get(p['id'], Decimal('0'))
        if p['cantidad'] < salidas:
            resultado['producto']['total'] += 1
            resultado['producto']['items'].append({
                'nombre': p['producto__nombre_comercial'],
                'stock': p['cantidad'],
                'salidas': salidas
            })
    
    # Envases
    stock_env = Inv_Envase.objects.values('id', 'envase__codigo_envase', 'cantidad')
    salidas_env = Movimiento_EE.objects.filter(
        vale__entrada=False,
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values('envase_embalaje_id').annotate(total_salidas=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))
    salidas_dict = {item['envase_embalaje_id']: item['total_salidas'] for item in salidas_env}
    for e in stock_env:
        salidas = salidas_dict.get(e['id'], Decimal('0'))
        if e['cantidad'] < salidas:
            resultado['envase']['total'] += 1
            resultado['envase']['items'].append({
                'nombre': e['envase__codigo_envase'],
                'stock': e['cantidad'],
                'salidas': salidas
            })
    
    # Insumos
    stock_ins = Inv_Insumos.objects.values('id', 'insumos__nombre', 'cantidad')
    salidas_ins = Movimiento_Ins.objects.filter(
        vale__entrada=False,
        vale__fecha_movimiento__range=[fecha_inicio, fecha_fin]
    ).values('insumo_id').annotate(total_salidas=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))
    salidas_dict = {item['insumo_id']: item['total_salidas'] for item in salidas_ins}
    for i in stock_ins:
        salidas = salidas_dict.get(i['id'], Decimal('0'))
        if i['cantidad'] < salidas:
            resultado['insumo']['total'] += 1
            resultado['insumo']['items'].append({
                'nombre': i['insumos__nombre'],
                'stock': i['cantidad'],
                'salidas': salidas
            })
    
    return resultado

def obtener_datos_produccion(fecha_inicio, fecha_fin):
    """
    Retorna tres diccionarios con datos de producción:
    - completadas: Produccion con estado 'Concluida-Conforme' (ajustar según tus choices)
    - rechazadas: estado 'Concluida-Rechazada'
    - en_proceso: estados que no son concluidas (ej. 'Planificada', 'Iniciando mezcla', etc.)
    Además, para cada grupo, devuelve el total de producciones y la suma de cantidad_real (litros).
    También devuelve los 10 productos más producidos por litros para cada grupo.
    """
    # Definir estados según tu modelo (ajusta según CHOICE_ESTADO_PROD)
    ESTADO_CONFORME = 'Concluida-Conforme'  # Ajusta
    ESTADO_RECHAZADA = 'Concluida-Rechazada'
    ESTADOS_EN_PROCESO = ['Planificada', 'Iniciando mezcla', 'En proceso']  # Ajusta según tus estados
    
    completadas = Produccion.objects.filter(
        estado=ESTADO_CONFORME,
        fecha_creacion__range=[fecha_inicio, fecha_fin]  # asumiendo que tienes fecha_creacion (ModeloBase)
    )
    rechazadas = Produccion.objects.filter(
        estado=ESTADO_RECHAZADA,
        fecha_creacion__range=[fecha_inicio, fecha_fin]
    )
    en_proceso = Produccion.objects.filter(
        estado__in=ESTADOS_EN_PROCESO,
        fecha_creacion__range=[fecha_inicio, fecha_fin]
    )
    
    def procesar_grupo(qs, label):
        total_prod = qs.count()
        total_litros = qs.aggregate(total=Coalesce(Sum('cantidad_real'), 0, output_field=DecimalField(max_digits=10, decimal_places=2)))['total']
        # Top 10 productos por litros (agrupando por catalogo_producto)
        top = qs.values('catalogo_producto__nombre_comercial').annotate(
            litros=Coalesce(Sum('cantidad_real'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
        ).order_by('-litros')[:10]
        top_list = [{'nombre': item['catalogo_producto__nombre_comercial'], 'litros': item['litros']} for item in top]
        return {
            'total_producciones': total_prod,
            'total_litros': total_litros,
            'top': top_list
        }
    
    return {
        'completadas': procesar_grupo(completadas, 'completadas'),
        'rechazadas': procesar_grupo(rechazadas, 'rechazadas'),
        'en_proceso': procesar_grupo(en_proceso, 'en_proceso'),
    }

def serializar_items(diccionario):
    """ for tipo, datos in diccionario.items():
        datos['items_json'] = json.dumps(datos['items'], default=str) """
    return diccionario
    
@login_required
def dashboard_view(request):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    # Fecha inicio por defecto: mes actual, pero para lento movimiento y bajo inventario usaremos el primer día del mes anterior.
    # Sin embargo, el usuario puede filtrar; usaremos las fechas del filtro para todo.
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    if fecha_inicio:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        except ValueError:
            fecha_inicio = primer_dia_mes
    else:
        fecha_inicio = primer_dia_mes
    if fecha_fin:
        try:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            fecha_fin = hoy
    else:
        fecha_fin = hoy

    # 1. Solicitudes pendientes (salidas pendientes) desglosadas por tipo
    solicitudes_pendientes = obtener_desglose_por_tipo_inventario(
        Movimiento_MP, 'materia_prima', 'nombre', fecha_inicio, fecha_fin, es_salida=True
    )
    # Para completar, también necesitamos los otros modelos: Movimiento_Prod, Movimiento_EE, Movimiento_Ins
    # Pero la función ya maneja cada modelo; la llamamos para cada uno y combinamos.
    # Mejor: Crear una función que recorra todos los modelos.
    # Refactorizo: Voy a construir un desglose unificado.
    
    # Función auxiliar para unificar todos los movimientos pendientes (salidas y entradas)
    def desglose_movimientos_pendientes(es_salida):
        modelos = [
            (Movimiento_MP, 'materia_prima', 'materia_prima__materia_prima__nombre'),
            (Movimiento_Prod, 'producto', 'producto__producto__nombre_comercial'),
            (Movimiento_EE, 'envase', 'envase_embalaje__codigo_envase'),
            (Movimiento_Ins, 'insumo', 'insumo__nombre')
        ]
        resultado = {}
        for modelo, tipo, nombre_campo in modelos:
            qs = modelo.objects.filter(
                vale__estado__in=['borrador', 'confirmado'],
                vale__entrada= not es_salida
            )
            if fecha_inicio and fecha_fin:
                qs = qs.filter(vale__fecha_movimiento__range=[fecha_inicio, fecha_fin])
            # Agrupar por el ID del inventario y sumar cantidad
            # Determinamos el campo de agrupación según el modelo
            if modelo == Movimiento_MP:
                id_field = 'materia_prima_id'
                nombre_agrupado = nombre_campo
            elif modelo == Movimiento_Prod:
                id_field = 'producto_id'
                nombre_agrupado = nombre_campo
            elif modelo == Movimiento_EE:
                id_field = 'envase_embalaje_id'
                nombre_agrupado = nombre_campo
            elif modelo == Movimiento_Ins:
                id_field = 'insumo_id'
                nombre_agrupado = nombre_campo
            else:
                continue
            items = qs.values(id_field, nombre_agrupado).annotate(
                total=Coalesce(Sum('cantidad'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ).order_by('-total')
            resultado[tipo] = {
                'total': sum(item['total'] for item in items),
                'items': [{'nombre': item[nombre_agrupado], 'cantidad': item['total']} for item in items]
            }
        return resultado
    
    solicitudes_pendientes = Vale_Movimiento_Almacen.objects.filter(
            tipo__in=['Solicitud', 'Venta', 'Solicitud envasado'], despachado=False, estado__in=['confirmado', 'borrador']
        ) #desglose_movimientos_pendientes(es_salida=True)
    
    solicitudes_ventas = solicitudes_pendientes.filter(tipo = 'Venta').count()
    solicitud_produccion = solicitudes_pendientes.filter(tipo = 'Solicitud').count()
    solicitud_envasado = solicitudes_pendientes.filter(tipo = 'Solicitud envasado').count()
    solicitudes_totales = solicitudes_pendientes = Vale_Movimiento_Almacen.objects.filter(
            despachado=False, estado__in=['confirmado', 'borrador']
        )
    
    rec_compras = Adquisicion.objects.filter(registrada=False).count()
    rec_prod = Vale_Movimiento_Almacen.objects.filter(estado='confirmado', tipo__in=['Producción terminada', 'Envasado', 'Producción rechazada']).count()
    recepciones_pendientes = Vale_Movimiento_Almacen.objects.filter(estado='confirmado').count() + rec_compras
    
    # 2. Lento movimiento (desde el primer día del mes anterior)
    # Para esto, definimos fecha_inicio_lento = primer día del mes anterior
    if hoy.month == 1:
        primer_dia_mes_anterior = date(hoy.year - 1, 12, 1)
        #last_day_last_month = date(hoy.year - 1, 12, 31)
    else:
        primer_dia_mes_anterior = hoy.replace(month=hoy.month - 1, day=1)
        #last_day_last_month = date(today.year, today.month - 1, calendar.monthrange(today.year, today.month - 1)[1])

    # Pero usamos las fechas del filtro para consistencia; si el usuario quiere otro rango, usamos esas.
    lento_movimiento = obtener_lento_movimiento(fecha_inicio, fecha_fin)
    
    # 3. Bajo inventario
    bajo_inventario = obtener_bajo_inventario(fecha_inicio, fecha_fin)
    
    # 4. Datos de producción
    datos_produccion = obtener_datos_produccion(fecha_inicio, fecha_fin)
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'solicitudes_pendientes': solicitudes_pendientes,
        'recepciones_pendientes': recepciones_pendientes,
        'lento_movimiento': lento_movimiento,
        'bajo_inventario': bajo_inventario,
        'produccion': datos_produccion,
        # También podemos incluir totales generales para mostrar en tarjetas
        
    }
    """ 'total_solicitudes': sum(v['total'] for v in solicitudes_pendientes.values()),
        'total_recepciones': sum(v['total'] for v in recepciones_pendientes.values()),
        'total_lento': sum(v['total'] for v in lento_movimiento.values()),
        'total_bajo': sum(v['total'] for v in bajo_inventario.values()), """
    
    context['solicitudes_pendientes'] = serializar_items(solicitudes_pendientes)
    context['recepciones_pendientes'] = serializar_items(recepciones_pendientes)
    context['lento_movimiento'] = serializar_items(lento_movimiento)
    context['bajo_inventario'] = serializar_items(bajo_inventario)

    # Serializar los tops de producción
    for key in ['completadas', 'rechazadas', 'en_proceso']:
        if 'top' in context['produccion'][key]:
            context['produccion'][key]['top_json'] = json.dumps(
                context['produccion'][key]['top'], default=str
            )

    return render(request, 'dashboard/dashboard.html', context)

def importar_productos_desde_api(request):
    url = "http://tienda.produccionesmuhia.ca/catalogo/listarGippro/"
    params = {
        'fields': 'gname,presentation,sku,is_feedstock,count,categories'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lanza excepción para errores HTTP

        productos_data = response.json()
        contador_nuevas = 1
        contador_nuevos = 1

        almacen = Almacen.objects.filter(nombre='Planta').first()

        for producto_data in productos_data:
            # Verificar si el producto ya existe por SKU
            is_feedstock = producto_data.get('is_feedstock', False)
            #print(producto_data.get('sku', ''))
            created = False
            codigon = producto_data.get('sku', '')
            categorias = producto_data.get('categories', '')
            categoria = categorias[0].get('name', '')
            if is_feedstock:
                materia_prima, created_mp = MateriaPrima.objects.update_or_create(                    
                    nombre=producto_data.get('gname', ''),
                    defaults={
                    'unidad_medida': producto_data.get('presentation', ''),
                    'tipo_materia_prima' : categoria.lower(),
                    }
                )
                
                materia_prima.save()
                
                """ vale = Vale_Movimiento_Almacen.objects.create(
                    almacen = almacen,
                    entrada = True
                ) """
                cantidad = decimal.Decimal(producto_data.get('count', '0'))
                if cantidad != 0:
                    try:
                        """  mov = Movimiento_MP.objects.create(
                            materia_prima=materia_prima,
                            vale=vale,  # Ejemplo: atributo fijo
                            cantidad=cantidad                        
                        ) """
                        """ if mov:
                            print('existe Movimiento_MP')
                        else:
                            print('Eres comemierda')
                        print('creado movimiento') """
                        inventario_mp, created_inv = Inv_Mat_Prima.objects.get_or_create(
                            materia_prima=materia_prima, almacen=almacen)
                        """ if created_inv:
                            print('Creado inventario')
                            print(inventario_mp.almacen)
                        else:
                            print('No fue ceado el inventario')
                            print(inventario_mp.almacen) """
                        """ if cantidad > inventario_mp.cantidad:
                            vale.entrada = True 
                            mov.cantidad = cantidad - inventario_mp.cantidad
                        else:
                            vale.entrada = False
                            mov.cantidad = inventario_mp.cantidad - cantidad
                        vale.save()
                        mov.save() """
                        inventario_mp.cantidad = cantidad
                        inventario_mp.save()
                    except Exception as e: #(ValueError, TypeError):
                        pass
                """ else:
                    print("No encontro cantidad") """
                if created_mp:
                    contador_nuevas += 1
                """ else:
                    print("No se creo nueva") """
                codigon = ''
            else:
                cant_vieja = 0
                formato_str = producto_data.get('presentation', '').lower()
                cap_str = ''
                for i in formato_str:
                    try:
                        if int(i) or i == '0':
                            cap_str = cap_str + i
                        else:
                            break
                    except:
                        break
                if cap_str == '':
                    capacidad = 0
                else:
                    capacidad = int(cap_str)
                if 'kg' in formato_str:
                    um = 'KG'
                elif 'ml' in formato_str:
                    um = 'ML'
                elif 'l' in formato_str:
                    um = 'L'
                elif 'granel' in formato_str:
                    capacidad = 0
                    um = 'L'
                else:
                    um = 'U'
                formato = Formato.objects.filter(unidad_medida=um, capacidad=capacidad).first()
                if not formato:
                    formato = Formato.objects.create(unidad_medida=um, capacidad=capacidad)
                """ else:
                    print('Ya encontro formato') """
                nomb_prod = producto_data.get('gname', '')
                producto = Producto.objects.filter(                    
                    nombre_comercial= nomb_prod
                ).first()
                if not producto:
                    try:
                        producto = Producto.objects.create(nombre_comercial = nomb_prod, costo=0.00)
                        created_prod = True
                    except Exception as e:
                        continue
                else:
                    created_prod = False
                    cant_vieja = producto.cantidad_total
                cantidad = decimal.Decimal(producto_data.get('count', '0'))
                if cantidad != 0:
                    try:
                        """ mov = Movimiento_Prod.objects.create(
                            producto=producto,
                            vale_e=vale,  # Ejemplo: atributo fijo
                            cantidad=cantidad                        
                        ) """
                        """ if mov:
                            print('existe Movimiento_Prod')
                        else:
                            print('Eres comemierda')
                        print('creado movimiento') """
                        inventario_prod, created_inv = Inv_Producto.objects.get_or_create(
                            producto=producto, almacen=almacen)
                        if created_inv:
                            fecha_actual = datetime.now()
                            fecha_codigo = fecha_actual.strftime('%y%m%d')
                            lote = f"{fecha_codigo}-{producto.codigo_3l}-0000-{str(formato)}"
                            inventario_prod.lote = lote
                            inventario_prod.formato = formato
                        else:
                            print('No fue ceado el inventario')
                            print(inventario_prod.almacen)
                        """ if cantidad > inventario_prod.cantidad:
                            vale.entrada = True 
                            mov.cantidad = cantidad - inventario_prod.cantidad
                        else:
                            vale.entrada = False
                            mov.cantidad = inventario_prod.cantidad - cantidad
                        vale.save()
                        mov.save() """
                        inventario_prod.cantidad = cantidad
                        inventario_prod.save()
                    except Exception as e: #(ValueError, TypeError):
                        pass
                """ else:
                    print("No encontro cantidad") """
                if created_prod:
                    contador_nuevos += 1
                """ else:
                    print("No se creo nueva") """
                codigon = ''
        messages.info(request, f"Se importaron {contador_nuevos} productos nuevos. Total procesados: {len(productos_data)}")
        return redirect('materia_prima:materia_prima_list')

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