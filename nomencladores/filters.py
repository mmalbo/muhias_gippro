import django_filters
from .almacen.models import *
from .planta.models import *

class Filtro_Almacen(django_filters.FilterSet):
    class Meta:
        model = Almacen
        fields = ['propio']

class Filtro_Planta(django_filters.FilterSet):
    class Meta:
        model = Planta
        fields = ['propio']