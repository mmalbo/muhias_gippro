# adquisiciones/templatetags/adquisicion_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiplica dos valores.
    Uso: {{ valor1|multiply:valor2 }}
    """
    print(f"DEBUG multiply: value={value}, type={type(value)}, arg={arg}, type={type(arg)}")
    try:
        # Si value o arg son None, retornar 0
        if value is None or arg is None:
            print("DEBUG multiply: None detected, returning 0")
            return 0
        
        # Convertir ambos a float para la multiplicación
        result = float(value) * float(arg)
        print(f"DEBUG multiply: result={result}")
        
        return result

    except (ValueError, TypeError, AttributeError):
        print(f"DEBUG multiply error: {e}")
        return 0

@register.filter
def format_currency(value):
    """Formatea un valor como moneda"""
    try:
        if value is None:
            return "$0.00"
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter(name='default_if_none')
def default_if_none(value, default):
    """Reemplaza None por un valor por defecto"""
    return value if value is not None else default