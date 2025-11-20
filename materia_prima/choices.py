# app/choices.py
from django.utils.translation import gettext_lazy as _
import json
import os
from django.conf import settings

ESTADOS = [
    ('adquirida', _('Adquirida')),
    ('produccion', _('Producción')),
    ('inventario', _('Inventario')),
    ('disponibleV', _('Disponible Venta')),
    ('reservada', _('Reservada')),
    ('vendida', _('Vendida')),
    ('entregada', _('Entregada')),
]

# Archivo donde se guardarán las opciones dinámicas
Fichero_tipos_dinamicos = os.path.join(settings.BASE_DIR, 'dynamic_choices.json')

Tipo_mat_prima = [
    ('bases', _('Bases')),
    ('colorantes', _('Color')),
    ('conservantes', _('Conservantes')),
    ('espesantes', _('Espesantes')),
    ('fragancias', _('Fragancias')),
    ('humectantes', _('Humectantes')),
    ('otros', _('Otros')),
    ('tensoactivos', _('Tensoactivos'))
]

# Cargar opciones dinámicas desde JSON
def _cargar_opciones_dinamicas():
    """Carga las opciones dinámicas desde el archivo JSON"""
    if os.path.exists(Fichero_tipos_dinamicos):
        try:
            with open(Fichero_tipos_dinamicos, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# Guardar opciones dinámicas en JSON
def _guardar_opciones_dinamicas(opciones):
    """Guarda las opciones dinámicas en el archivo JSON"""
    try:
        with open(Fichero_tipos_dinamicos, 'w', encoding='utf-8') as f:
            json.dump(opciones, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# Opciones combinadas (base + dinámicas)
def obtener_tipos_materia_prima():
    """Devuelve todas las categorías (base + dinámicas)"""
    opciones_dinamicas = _cargar_opciones_dinamicas()
    return Tipo_mat_prima + opciones_dinamicas

# Funciones para gestión dinámica
def agregar_tipo_materia_prima(valor, etiqueta):
    """Agrega una nueva categoría dinámica"""
    opciones = _cargar_opciones_dinamicas()
    nueva_opcion = (valor, etiqueta)
    
    # Verificar si ya existe
    if nueva_opcion not in opciones and (valor, etiqueta) not in Tipo_mat_prima:
        opciones.append(nueva_opcion)
        return _guardar_opciones_dinamicas(opciones)
    return False

def eliminar_tipo_materia_prima(valor):
    """Elimina una categoría dinámica"""
    opciones = _cargar_opciones_dinamicas()
    opciones = [op for op in opciones if op[0] != valor]
    return _guardar_opciones_dinamicas(opciones)

def obtener_categoria_por_valor(valor):
    """Obtiene la etiqueta de una categoría por su valor"""
    todas_categorias = obtener_tipos_materia_prima()
    for cat_valor, cat_etiqueta in todas_categorias:
        if cat_valor == valor:
            return cat_etiqueta
    return _('Desconocida')

def existe_tipo_materia_prima(valor):
    """Verifica si una categoría existe"""
    todas_categorias = obtener_tipos_materia_prima()
    return any(cat_valor == valor for cat_valor, _ in todas_categorias)