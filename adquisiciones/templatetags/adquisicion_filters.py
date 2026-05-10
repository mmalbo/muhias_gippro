# adquisiciones/templatetags/adquisicion_filters.py
from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiplica dos valores.
    Uso: {{ valor1|multiply:valor2 }}
    """
    try:
        # Convertir ambos valores a float para la multiplicación
        result = float(value) * float(arg)
        return result
    except (ValueError, TypeError):
        return 0

@register.filter(name='default_if_none')
def default_if_none(value, default):
    """Reemplaza None por un valor por defecto"""
    return value if value is not None else default