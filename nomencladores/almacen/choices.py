from django.utils.translation import gettext_lazy as _
import json
import os
from django.conf import settings

Conceptos = [
    ('inventario', _('Inventario')),
    ('puntoV', _('Punto de Venta')),
    ('cooperada', _('Cooperada')),
    ('consignacion', _('Consignación')),
    ('planta', _('Planta de producción')),
    ('mixta', _('Mixta')),    
]

# Archivo donde se guardarán las opciones dinámicas
Fichero_concept_dinamicos = os.path.join(settings.BASE_DIR, 'dynamic_concept_alm.json')


# Cargar opciones dinámicas desde JSON
def _cargar_opciones_dinamicas():
    """Carga las opciones dinámicas desde el archivo JSON"""
    if os.path.exists(Fichero_concept_dinamicos):
        try:
            with open(Fichero_concept_dinamicos, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# Guardar opciones dinámicas en JSON
def _guardar_opciones_dinamicas(opciones):
    """Guarda las opciones dinámicas en el archivo JSON"""
    try:
        with open(Fichero_concept_dinamicos, 'w', encoding='utf-8') as f:
            json.dump(opciones, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# Opciones combinadas (base + dinámicas)
def obtener_conceptos_almacen():
    """Devuelve todas las categorías (base + dinámicas)"""
    opciones_dinamicas = _cargar_opciones_dinamicas()
    return Conceptos + opciones_dinamicas

# Funciones para gestión dinámica
def agregar_opciones_dinamicas(valor, etiqueta):
    """Agrega una nueva categoría dinámica"""
    opciones = _cargar_opciones_dinamicas()
    nueva_opcion = (valor, etiqueta)
    
    # Verificar si ya existe
    if nueva_opcion not in opciones and (valor, etiqueta) not in Conceptos:
        opciones.append(nueva_opcion)
        return _guardar_opciones_dinamicas(opciones)
    return False

def eliminar_opciones_dinamicas(valor):
    """Elimina una categoría dinámica"""
    opciones = _cargar_opciones_dinamicas()
    opciones = [op for op in opciones if op[0] != valor]
    return _guardar_opciones_dinamicas(opciones)

def obtener_categoria_por_valor(valor):
    """Obtiene la etiqueta de una categoría por su valor"""
    todas_categorias = obtener_conceptos_almacen()
    for cat_valor, cat_etiqueta in todas_categorias:
        if cat_valor == valor:
            return cat_etiqueta
    return _('Desconocida')

def existe_conceptos_almacen(valor):
    """Verifica si una categoría existe"""
    todas_categorias = obtener_conceptos_almacen()
    return any(cat_valor == valor for cat_valor, _ in todas_categorias)