import django_filters
from .formato.models import *
from .tipo_envase_embalaje.models import *
from .caja.models import *
from .pomo.models import *
from .tanque.models import *
from .tapa.models import *


class Filtro_Formato(django_filters.FilterSet):
    class Meta:
        model = Formato
        fields = ['unidad_medida', 'capacidad',]

class Filtro_Tipo(django_filters.FilterSet):
    class Meta:
        model = TipoEnvaseEmbalaje
        fields = ['nombre', 'codigo',]

class Filtro_Caja(django_filters.FilterSet):
    class Meta:
        model = Caja
        fields = ['nombre', 'tamanno', 'material',]

class Filtro_Pomo(django_filters.FilterSet):
    class Meta:
        model = Pomo
        fields = ['nombre', 'color', 'forma', 'material',]

class Filtro_Tanque(django_filters.FilterSet):
    class Meta:
        model = Tanque
        fields = ['nombre', 'color', 'material',]

class Filtro_Tapa(django_filters.FilterSet):
    class Meta:
        model = Tapa
        fields = ['nombre', 'color', 'descripcion',]