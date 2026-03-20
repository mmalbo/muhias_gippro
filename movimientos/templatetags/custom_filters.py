# tu_app/templatetags/custom_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplica value por arg"""
    try:
        # Si ambos son Decimal o float
        if isinstance(value, (Decimal, float)) and isinstance(arg, (Decimal, float, int)):
            return float(value) * float(arg)
        # Convertir a float si es posible
        return float(value) * float(arg)
    except (ValueError, TypeError, AttributeError):
        return 0

@register.filter
def format_currency(value):
    """Formatea un valor como moneda"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario"""
    return dictionary.get(key, '')

@register.filter
def split(value, delimiter=','):
    """Divide un string por un delimitador"""
    return value.split(delimiter)

@register.filter(name='abs')
def absolute_value(value):
    """Valor absoluto"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, total):
    """Calcula porcentaje"""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0