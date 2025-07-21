import django_filters
from .models import *

class FiltroAdquisicion(django_filters.FilterSet):
    class Meta:
        model = Adquisicion
        fields = ['fecha_compra', 'importada', 'currency']