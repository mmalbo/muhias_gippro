# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from utils.models import Notification
from produccion.models import Produccion, Prod_Inv_MP
#from inventario.models import Inv_Mat_Prima

@receiver(post_save, sender=Produccion)
def notificar_produccion_creada(sender, instance, created, **kwargs):
    
    """Signal para notificar cuando se crea una nueva producción"""
    if created:
       # Obtener las materias primas involucradas (si ya están guardadas)
        materias_primas = Prod_Inv_MP.objects.filter(lote_prod=instance).__getattribute__
        
        # 1. NOTIFICACIÓN PARA RESPONSABLES DE ALMACÉN
        notificar_responsables_almacen(instance, materias_primas)
        
        # 2. NOTIFICACIÓN PARA GRUPO ADMINISTRATIVO
        notificar_grupo_administrativo(instance, materias_primas)

def notificar_responsables_almacen(produccion, materias_primas):
    """Notificar a los responsables de almacén de las materias primas involucradas"""

    try:
        # Obtener almacenes únicos de las materias primas
        almacenes_ids = materias_primas.values_list('almacen' ).distinct()
            #, flat=True)
        print(almacenes_ids)
        # Buscar usuarios responsables de estos almacenes
        # Asumiendo que tienes un modelo Almacen con campo 'responsable'
        from nomencladores.almacen.models import Almacen
        responsables = User.objects.filter(
            almacenes_responsable__id__in=almacenes_ids,
        ).distinct()
        print(responsables)
        # Si no hay responsables específicos, notificar al grupo "Almacen"
        if not responsables.exists():
            try:
                grupo_almacen = Group.objects.get(name='Almaceneros')
                responsables = grupo_almacen.user_set.filter(is_active=True)
            except Group.DoesNotExist:
                # Si no existe el grupo, notificar a supervisores
                responsables = User.objects.filter(
                    groups__name__in=['Presidencia-Admin', 'Comerciales'],
                    is_active=True
                ).distinct()
        
        # Crear mensaje específico para almacén
        mensaje_almacen = (
            f'Nueva producción creada que requiere materiales de tus almacenes. '
            f'Producto: {produccion.catalogo_producto.nombre_comercial}, '
            f'Lote: {produccion.lote}, '
            f'Cantidad estimada: {produccion.cantidad_estimada}. '
        )
        
        # Agregar detalles de materias primas si están disponibles
        if materias_primas.exists():
            mensaje_almacen += '\n\nMateriales requeridos:\n'
            for mp in materias_primas:
                mensaje_almacen += f'• {mp.materia_prima.nombre}: {mp.cantidad} {mp.materia_prima.unidad_medida} (Almacén: {mp.almacen.nombre})\n'
        
        for responsable in responsables:
            Notification.objects.create(
                usuario=responsable,
                #tipo='produccion_creada',
                #nivel='warning',  # Warning porque requiere acción
                #titulo=f'📦 Producción Requiere Materiales - Lote {produccion.lote}',
                mensaje=mensaje_almacen,
               #relacion_contenido_type=contenido_type,
                #relacion_contenido_id=produccion.id
            )
    except Exception as e:
        print(f"Error notificando responsables de almacén: {e}")

def notificar_grupo_administrativo(produccion, materias_primas):
    """Notificar al grupo administrativo sobre la nueva producción"""
    try:
        # Buscar grupo administrativo
        try:
            grupo_administrativo = Group.objects.get(name='Presidencia-Admin')
            usuarios_administrativos = grupo_administrativo.user_set.filter(is_active=True)
        except Group.DoesNotExist:
            # Si no existe el grupo, usar otros grupos administrativos comunes
            usuarios_administrativos = User.objects.filter(
                groups__name__in=['Presidencia-Admin'], is_active=True
            ).distinct()
        # Si no hay usuarios administrativos, notificar a staff
        if not usuarios_administrativos.exists():
            usuarios_administrativos = User.objects.filter(is_staff=True, is_active=True)
        
        # Crear mensaje para administrativo (más enfocado en costos y planificación)
        costo_total_materias_primas = sum(
            float(mp.cantidad) * float(mp.materia_prima.costo) 
            for mp in materias_primas
        ) if materias_primas.exists() else 0
        
        mensaje_administrativo = (
            f'Nueva producción planificada. '
             f'Producto: {produccion.catalogo_producto.nombre_comercial}, '
            f'Lote: {produccion.lote}, '
            f'Cantidad estimada: {produccion.cantidad_estimada}, '
            f'Costo producción: ${produccion.costo}, '
            f'Costo estimado materias primas: ${costo_total_materias_primas:.2f}, '
            f'Planta: {produccion.planta.nombre}.'
        )
        
        # Agregar resumen de materias primas si están disponibles
        if materias_primas.exists():
            mensaje_administrativo += f'\n\nInsumos: {materias_primas.count()} requeridos.'
            for usuario in usuarios_administrativos:
                Notification.objects.create(
                    usuario=usuario,#tipo='produccion_creada',#nivel='info',
                    #titulo=f'📊 Nueva Producción Planificada - Lote {produccion.lote}'
                    # ,mensaje=mensaje_administrativo,
                    # #relacion_contenido_type=contenido_type,#relacion_contenido_id=produccion.id
            )
            
    except Exception as e:
        print(f"Error notificando grupo administrativo: {e}")

"""@receive r(post_save, sender=Produccion)
def notificar_cambio_estado_produccion(sender, instance, **kwargs):
    Signal para notificar cambios de estado en la producción
    if not kwargs.get('created', False):  # Solo para actualizaciones
        # Verificar si el estado cambió
        if instance.tracker.has_changed('estado'):
            estado_anterior = instance.tracker.previous('estado')
            estado_nuevo = instance.estado
            
            # Definir niveles y mensajes según el cambio de estado
            config_notificacion = {
                'pendiente': {'nivel': 'info', 'accion': 'planificada'},
                'en_proceso': {'nivel': 'warning', 'accion': 'iniciada'},
                'completada': {'nivel': 'success', 'accion': 'completada'},
                'cancelada': {'nivel': 'error', 'accion': 'cancelada'},
            }
            
            if estado_nuevo in config_notificacion:
                config = config_notificacion[estado_nuevo]
                
                usuarios_notificar = User.objects.filter(
                    is_active=True,
                    groups__name__in=['Supervisores', 'Produccion']
                ).distinct()
                
                contenido_type = ContentType.objects.get_for_model(instance)
                
                for usuario in usuarios_notificar:
                    Notificacion.objects.create(
                        usuario=usuario,
                        tipo=f'produccion_{config["accion"]}',
                        nivel=config['nivel'],
                        titulo=f'Producción {config["accion"].title()} - Lote {instance.lote}',
                        mensaje=(
                            f'La producción del producto "{instance.catalogo_producto.nombre}" '
                            f'ha cambiado de estado de "{estado_anterior}" a "{estado_nuevo}". '
                            f'Lote: {instance.lote}'
                        ),
                        relacion_contenido_type=contenido_type,
                        relacion_contenido_id=instance.id
                    ) """