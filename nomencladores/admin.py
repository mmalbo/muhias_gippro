from django.contrib import admin
from nomencladores.planta.models import Planta
from nomencladores.color.models import Color
from nomencladores.almacen.models import Almacen


# Register your models here.
@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    pass


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    pass


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    pass
