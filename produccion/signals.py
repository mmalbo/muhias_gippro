# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from utils.models import Notification
from produccion.models import Produccion, Prod_Inv_MP
from usuario.models import CustomUser
#from inventario.models import Inv_Mat_Prima

@receiver(post_save, sender=Produccion)
def notificar_produccion_creada(sender, instance, created, **kwargs):
    
    """Signal para notificar cuando se crea una nueva producción"""
    if created:
        pass
       # Obtener las materias primas involucradas (si ya están guardadas)
        #materias_primas_info = obtener_materias_primas_de_produccion(instance)
        
        # 1. NOTIFICACIÓN PARA RESPONSABLES DE ALMACÉN
        #notificar_responsables_almacen(instance, materias_primas_info)
        
        # 2. NOTIFICACIÓN PARA GRUPO ADMINISTRATIVO
        #notificar_grupo_administrativo(instance, materias_primas_info)

def obtener_materias_primas_de_produccion(produccion):
    """Obtener información de materias primas a través de Prod_Inv_MP"""
    try:
        # Navegar: Produccion -> Prod_Inv_MP -> Inv_Mat_Prima
        relaciones_mp = Prod_Inv_MP.objects.filter(lote_prod=produccion)
        materias_primas_info = []
        for relacion in relaciones_mp:
            inv_mp = relacion.inv_materia_prima  # Esto es un objeto Inv_Mat_Prima
            
            materias_primas_info.append({
                'materia_prima': inv_mp.materia_prima,
                'almacen': inv_mp.almacen,
                'cantidad_necesaria': relacion.cantidad_materia_prima,  # De Prod_Inv_MP
                'cantidad_disponible': inv_mp.cantidad,  # De Inv_Mat_Prima
                'unidad_medida': inv_mp.materia_prima.unidad_medida,
            })
        
        return materias_primas_info
        
    except Exception as e:
        print(f"Error obteniendo materias primas de producción: {e}")
        return []


def notificar_responsables_almacen(produccion, materias_primas_info):
    """Notificar a los responsables de almacén de las materias primas involucradas"""

    try:
        # Obtener almacenes únicos de las materias primas
        almacenes_ids = list(set([mp['almacen'].id for mp in materias_primas_info]))
        
        # Buscar usuarios responsables de estos almacenes
        # Asumiendo que tienes un modelo Almacen con campo 'responsable'
        responsables = CustomUser.objects.filter(
            almacen__id__in=almacenes_ids,
        ).distinct()
        # Si no hay responsables específicos, notificar al grupo "Almacen"
        if not responsables.exists():
            try:
                responsables = CustomUser.objects.filter(
                    groups__name__in=['Almaceneros'],
                    is_active=True
                ).distinct()
                #grupo_almacen = Group.objects.get(name='Almaceneros')
                #responsables = grupo_almacen.user_set.filter(is_active=True)
            except Group.DoesNotExist:
                # Si no existe el grupo, notificar a supervisores
                responsables = CustomUser.objects.filter(
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
        if len(materias_primas_info)>0:
            mensaje_almacen += '\n\nMateriales requeridos:\n'
            for mp in materias_primas_info:
                mensaje_almacen += f'• {mp.materia_prima.nombre}: {mp.cantidad} {mp.materia_prima.unidad_medida} (Almacén: {mp.almacen.nombre})\n'

        print(len(materias_primas_info))
        
        for responsable in responsables:
            print(responsable)
            Notification.objects.create(
                user=responsable,
                #tipo='produccion_creada',
                #nivel='warning',  # Warning porque requiere acción
                #titulo=f'📦 Producción Requiere Materiales - Lote {produccion.lote}',
                message=mensaje_almacen,
                link = f'/movimientos/salida_produccion/{produccion.id}/'
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

