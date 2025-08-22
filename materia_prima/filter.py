import django_filters
from .models import *
from .tipo_materia_prima.models import *

class Filtro_Tipo(django_filters.FilterSet):
    class Meta:
        model = TipoMateriaPrima
        fields = ['nombre', 'tipo', ]